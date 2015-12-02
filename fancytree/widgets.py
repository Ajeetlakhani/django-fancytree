from itertools import chain

from django import forms
from django.conf import settings
from django.forms.widgets import Widget
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.datastructures import MultiValueDict, MergeDict
from mptt.templatetags.mptt_tags import cache_tree_children


try:
    import simplejson as json
except ImportError:
    import json


def get_doc(node, values):
    if hasattr(node, "get_doc"):
        return node.get_doc(values)
    if hasattr(node, "name"):
        name = node.name
    else:
        name = unicode(node)
    doc = {"title": name, "key": node.pk}
    if str(node.pk) in values:
        doc['selected'] = True
        doc['expand'] = True
    return doc

def recursive_node_to_dict(node, values):
    result = get_doc(node, values)
    children = [recursive_node_to_dict(c, values) for c in node.get_children()]
    if children:
        expand = [c for c in children if c.get('selected', False)]
        if expand:
            result["expand"] = True
        result["folder"] = True
        result['children'] = children
    return result

def get_tree(nodes, values):
    root_nodes = cache_tree_children(nodes)
    return [recursive_node_to_dict(n, values) for n in root_nodes]

class FancyTreeWidget(Widget):
    def __init__(self,model, attrs=None, choices=(), queryset=None, select_mode=1):
        super(FancyTreeWidget, self).__init__(attrs)
        self.queryset = queryset
        self.select_mode = select_mode
        self.choices = list(choices)

        self.app_label= model._meta.app_label,

        self.model=model;


    def value_from_datadict(self, data, files, name):
        return data.get(name, None)

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = []
        else:
            current_name = self.model.objects.get(id=value)
            current_value = value

        if not isinstance(value, (list, tuple)):
            value = [value]
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        if has_id:
            output = [u'<div><p><input id="fancytree_search_box" type="text" \
                placeholder="Search Category"> <span id="matches"></span>  &nbsp;&nbsp;&nbsp; Current :<a href="/admin/%s"> <span>%s</span></a> \
                &nbsp;|&nbsp; Selected : <span id="selectedValue"> None </span> \
                </p><div id="newSearchTree"></div></div><br>\
                <div id="%s"></div>' % (str(self.model._meta.app_label)+'/'+str(self.model.__name__)+'/'+str(current_value),
                    str(current_name).title(), attrs['id'])]
            id_attr = u' id="%s_checkboxes"' % (attrs['id'])
        else:
            output = [u'<div></div>']
            id_attr = u''
        output.append(u'<ul class="fancytree_checkboxes"%s>' % id_attr)
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], option_value))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(
                u'<li><label%s>%s %s</label></li>' % (label_for, rendered_cb, option_label)
            )
        output.append(u'</ul>')
        output.append(u'<script type="text/javascript">')
        js_data_var = 'fancytree_data_%s' % (attrs['id'].replace('-', '_'))
        if has_id:
            output.append(u'var %s = %s;' % (
                js_data_var,
                json.dumps(get_tree(self.queryset, str_values))
            ))
            output.append(
                """
                $(".fancytree_checkboxes").hide();
                $("#%(id)s").attr("folder-clicked",false);
                $(function() {
                    $("#%(id)s").fancytree({
                        extensions: ["filter"],
                        quicksearch: true,
                        filter: {
                            autoApply: true,  // Re-apply last filter if lazy data is loaded
                            //counter: true,  // Show a badge with number of matching child nodes near parent icons
                            fuzzy: false,  // Match single characters in order, e.g. 'fb' will match 'FooBar'
                            //hideExpandedCounter: true,  // Hide counter badge, when parent is expanded
                            highlight: true,  // Highlight matches by wrapping inside <mark> tags
                            mode: "hide"  // Grayout unmatched nodes (pass "hide" to remove unmatched node instead)
                        }, 
                        checkbox: true,
                        selectMode: %(select_mode)d,
                        source: %(js_var)s,
                          lazyLoad: function(event, data) {
                            data.result = %(js_var)s
                          },
                        debugLevel: %(debug)d,
                        select: function(event, data) {
                            var selNodes = data.tree.getSelectedNodes();
                            var selKeys = $.map(selNodes, function(node){
                                   $('#%(id)s_' + (node.key)).prop('checked', true);
                                   $('#selectedValue').html(node.title)
                                   return node.key;
                            });
                        },
                        click: function(event, data) {
                            var node = data.node;               
                          
                           $('li span.fancytree-title').click(function(){
                               $("#%(id)s").attr("folder-clicked",true);
                            })
                            var folderClicked = $("#%(id)s").attr("folder-clicked");
                            if(!folderClicked){
                                console.log($("#%(id)s").attr("folder-clicked"));
                                $('#selectedValue').html("None");
                            }else{
                               $('li span.fancytree-checkbox').click(function(){
                                    $('#selectedValue').html("None");
                                });
                            }

                            if (event.targetType == "fancytreeclick"){
                                node.toggleSelected();
                            }
                        },
                    });
                    function treeFiltering() {
                        var tree = $('#%(id)s').fancytree('getTree');
                
                        $("#fancytree_search_box").keyup(function(e){
                          var n,
                            opts = {
                              autoExpand: $("#autoExpand").is(":checked"),
                              leavesOnly: false
                            },
                            match = $(this).val();

                          if(e && e.which === $.ui.keyCode.ESCAPE || $.trim(match) === ""){
                            $("button#btnResetSearch").click();
                            return;
                          }
                          if($("#regex").is(":checked")) {
                            n = tree.filterNodes(function(node) {
                              return new RegExp(match, "i").test(node.title);
                            }, opts);
                          } else {
                            n = tree.filterNodes(match, opts);
                          }
                          $("button#btnResetSearch").attr("disabled", false);
                          $("span#matches").text("(" + n + " matches)");
                        }).focus();

                    }
                    treeFiltering();
                 });
   
                var searchTreeArray= %(js_var)s;
                var tree_id=%(id)s;
                var model="%(model)s";
                var app_label="%(app_label)s";


                """ % {
                    'id': attrs['id'],
                    'js_var': js_data_var,
                    'debug': settings.DEBUG and 1 or 0,
                    'select_mode': self.select_mode,
                    'model': self.model,
                    'app_label':self.app_label,
                }
            );
        output.append(u'</script>')
        return mark_safe(u'\n'.join(output))

    class Media:
        css = {
            'all': ('fancytree/skin-vista/ui.fancytree.css',)
        }
        js = (
            'fancytree/jquery.fancytree.min.js',
            'fancytree/fancytree.filter.js',
            # 'fancytree/fancytree.js',
        )
