from textwrap import dedent

from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template

# isort: off
from .django_test_setup import *  # NOQA
from .testutils import Django30CompatibleSimpleTestCase as SimpleTestCase

# isort: on

from django_components import component


class ComponentTest(SimpleTestCase):
    def test_empty_component(self):
        class EmptyComponent(component.Component):
            pass

        with self.assertRaises(ImproperlyConfigured):
            EmptyComponent("empty_component").get_template(Context({}))

    def test_simple_component(self):
        class SimpleComponent(component.Component):
            template_name = "simple_template.html"

            def get_context_data(self, variable=None):
                return {
                    "variable": variable,
                }

            class Media:
                css = "style.css"
                js = "script.js"

        comp = SimpleComponent("simple_component")
        context = Context(comp.get_context_data(variable="test"))

        self.assertHTMLEqual(
            comp.render_dependencies(),
            dedent(
                """
            <link href="style.css" media="all" rel="stylesheet">
            <script src="script.js"></script>
        """
            ).strip(),
        )

        self.assertHTMLEqual(
            comp.render(context),
            dedent(
                """
            Variable: <strong>test</strong>
        """
            ).lstrip(),
        )

    def test_css_only_component(self):
        class SimpleComponent(component.Component):
            template_name = "simple_template.html"

            class Media:
                css = "style.css"

        comp = SimpleComponent("simple_component")

        self.assertHTMLEqual(
            comp.render_dependencies(),
            dedent(
                """
            <link href="style.css" media="all" rel="stylesheet">
        """
            ).strip(),
        )

    def test_js_only_component(self):
        class SimpleComponent(component.Component):
            template_name = "simple_template.html"

            class Media:
                js = "script.js"

        comp = SimpleComponent("simple_component")

        self.assertHTMLEqual(
            comp.render_dependencies(),
            dedent(
                """
            <script src="script.js"></script>
        """
            ).strip(),
        )

    def test_empty_media_component(self):
        class SimpleComponent(component.Component):
            template_name = "simple_template.html"

            class Media:
                pass

        comp = SimpleComponent("simple_component")

        self.assertHTMLEqual(comp.render_dependencies(), "")

    def test_missing_media_component(self):
        class SimpleComponent(component.Component):
            template_name = "simple_template.html"

        comp = SimpleComponent("simple_component")

        self.assertHTMLEqual(comp.render_dependencies(), "")

    def test_component_with_list_of_styles(self):
        class MultistyleComponent(component.Component):
            class Media:
                css = ["style.css", "style2.css"]
                js = ["script.js", "script2.js"]

        comp = MultistyleComponent("multistyle_component")

        self.assertHTMLEqual(
            comp.render_dependencies(),
            dedent(
                """
            <link href="style.css" media="all" rel="stylesheet">
            <link href="style2.css" media="all" rel="stylesheet">
            <script src="script.js"></script>
            <script src="script2.js"></script>
        """
            ).strip(),
        )

    def test_component_with_filtered_template(self):
        class FilteredComponent(component.Component):
            template_name = "filtered_template.html"

            def get_context_data(self, var1=None, var2=None):
                return {
                    "var1": var1,
                    "var2": var2,
                }

        comp = FilteredComponent("filtered_component")
        context = Context(comp.get_context_data(var1="test1", var2="test2"))

        self.assertHTMLEqual(
            comp.render(context),
            dedent(
                """
            Var1: <strong>test1</strong>
            Var2 (uppercased): <strong>TEST2</strong>
        """
            ).lstrip(),
        )

    def test_component_with_dynamic_template(self):
        class SvgComponent(component.Component):
            def get_context_data(self, name, css_class="", title="", **attrs):
                return {
                    "name": name,
                    "css_class": css_class,
                    "title": title,
                    **attrs,
                }

            def get_template_name(self, context):
                return f"svg_{context['name']}.svg"

        comp = SvgComponent("svg_component")
        self.assertHTMLEqual(
            comp.render(Context(comp.get_context_data(name="dynamic1"))),
            dedent(
                """\
                <svg>Dynamic1</svg>
            """
            ),
        )
        self.assertHTMLEqual(
            comp.render(Context(comp.get_context_data(name="dynamic2"))),
            dedent(
                """\
                <svg>Dynamic2</svg>
            """
            ),
        )


class InlineComponentTest(SimpleTestCase):
    def test_inline_html_component(self):
        class InlineHTMLComponent(component.Component):
            template = "<div class='inline'>Hello Inline</div>"

        comp = InlineHTMLComponent("inline_html_component")
        self.assertHTMLEqual(
            comp.render(Context({})),
            "<div class='inline'>Hello Inline</div>",
        )

    def test_html_and_css_only(self):
        class HTMLCSSComponent(component.Component):
            template = "<div class='html-css-only'>Content</div>"
            css = ".html-css-only { color: blue; }"

        comp = HTMLCSSComponent("html_css_component")
        self.assertHTMLEqual(
            comp.render(Context({})),
            "<div class='html-css-only'>Content</div>",
        )
        self.assertHTMLEqual(
            comp.render_css_dependencies(),
            "<style>.html-css-only { color: blue; }</style>",
        )

    def test_html_and_js_only(self):
        class HTMLJSComponent(component.Component):
            template = "<div class='html-js-only'>Content</div>"
            js = "console.log('HTML and JS only');"

        comp = HTMLJSComponent("html_js_component")
        self.assertHTMLEqual(
            comp.render(Context({})),
            "<div class='html-js-only'>Content</div>",
        )
        self.assertHTMLEqual(
            comp.render_js_dependencies(),
            "<script>console.log('HTML and JS only');</script>",
        )

    def test_html_string_with_css_js_files(self):
        class HTMLStringFileCSSJSComponent(component.Component):
            template = "<div class='html-string-file'>Content</div>"

            class Media:
                css = "path/to/style.css"
                js = "path/to/script.js"

        comp = HTMLStringFileCSSJSComponent(
            "html_string_file_css_js_component"
        )
        self.assertHTMLEqual(
            comp.render(Context({})),
            "<div class='html-string-file'>Content</div>",
        )
        self.assertHTMLEqual(
            comp.render_dependencies(),
            dedent(
                """\
                <link href="path/to/style.css" media="all" rel="stylesheet">
                <script src="path/to/script.js"></script>
            """
            ),
        )

    def test_html_js_string_with_css_file(self):
        class HTMLStringFileCSSJSComponent(component.Component):
            template = "<div class='html-string-file'>Content</div>"
            js = "console.log('HTML and JS only');"

            class Media:
                css = "path/to/style.css"

        comp = HTMLStringFileCSSJSComponent(
            "html_string_file_css_js_component"
        )
        self.assertHTMLEqual(
            comp.render(Context({})),
            "<div class='html-string-file'>Content</div>",
        )
        self.assertHTMLEqual(
            comp.render_dependencies(),
            dedent(
                """\
                <link href="path/to/style.css" media="all" rel="stylesheet">
                <script>console.log('HTML and JS only');</script>
                """
            ),
        )

    def test_html_css_string_with_js_file(self):
        class HTMLStringFileCSSJSComponent(component.Component):
            template = "<div class='html-string-file'>Content</div>"
            css = ".html-string-file { color: blue; }"

            class Media:
                js = "path/to/script.js"

        comp = HTMLStringFileCSSJSComponent(
            "html_string_file_css_js_component"
        )
        self.assertHTMLEqual(
            comp.render(Context({})),
            "<div class='html-string-file'>Content</div>",
        )
        self.assertHTMLEqual(
            comp.render_dependencies(),
            dedent(
                """\
                <style>.html-string-file { color: blue; }</style><script src="path/to/script.js"></script>
                """
            ),
        )

    def test_component_with_variable_in_html(self):
        class VariableHTMLComponent(component.Component):
            def get_template(self, context):
                return Template(
                    "<div class='variable-html'>{{ variable }}</div>"
                )

        comp = VariableHTMLComponent("variable_html_component")
        context = Context({"variable": "Dynamic Content"})
        self.assertHTMLEqual(
            comp.render(context),
            "<div class='variable-html'>Dynamic Content</div>",
        )


class ComponentMediaTests(SimpleTestCase):
    def test_component_media_with_strings(self):
        class SimpleComponent(component.Component):
            class Media:
                css = "path/to/style.css"
                js = "path/to/script.js"

        comp = SimpleComponent("")
        self.assertHTMLEqual(
            comp.render_dependencies(),
            dedent(
                """\
                <link href="path/to/style.css" media="all" rel="stylesheet">
                <script src="path/to/script.js"></script>
            """
            ),
        )

    def test_component_media_with_lists(self):
        class SimpleComponent(component.Component):
            class Media:
                css = ["path/to/style.css", "path/to/style2.css"]
                js = ["path/to/script.js"]

        comp = SimpleComponent("")
        self.assertHTMLEqual(
            comp.render_dependencies(),
            dedent(
                """\
                <link href="path/to/style.css" media="all" rel="stylesheet">
                <link href="path/to/style2.css" media="all" rel="stylesheet">
                <script src="path/to/script.js"></script>
            """
            ),
        )

    def test_component_media_with_dict_and_list(self):
        class SimpleComponent(component.Component):
            class Media:
                css = {
                    "all": "path/to/style.css",
                    "print": ["path/to/style2.css"],
                    "screen": "path/to/style3.css",
                }
                js = ["path/to/script.js"]

        comp = SimpleComponent("")
        self.assertHTMLEqual(
            comp.render_dependencies(),
            dedent(
                """\
                <link href="path/to/style.css" media="all" rel="stylesheet">
                <link href="path/to/style2.css" media="print" rel="stylesheet">
                <link href="path/to/style3.css" media="screen" rel="stylesheet">
                <script src="path/to/script.js"></script>
            """
            ),
        )

    def test_component_media_with_dict_with_list_and_list(self):
        class SimpleComponent(component.Component):
            class Media:
                css = {"all": ["path/to/style.css"]}
                js = ["path/to/script.js"]

        comp = SimpleComponent("")
        self.assertHTMLEqual(
            comp.render_dependencies(),
            dedent(
                """\
                <link href="path/to/style.css" media="all" rel="stylesheet">
                <script src="path/to/script.js"></script>
            """
            ),
        )


class ComponentIsolationTests(SimpleTestCase):
    def setUp(self):
        class SlottedComponent(component.Component):
            template_name = "slotted_template.html"

        component.registry.register("test", SlottedComponent)

    def test_instances_of_component_do_not_share_slots(self):
        template = Template(
            """
            {% load component_tags %}
            {% component_block "test" %}
                {% fill "header" %}Override header{% endfill %}
            {% endcomponent_block %}
            {% component_block "test" %}
                {% fill "main" %}Override main{% endfill %}
            {% endcomponent_block %}
            {% component_block "test" %}
                {% fill "footer" %}Override footer{% endfill %}
            {% endcomponent_block %}
        """
        )

        template.render(Context({}))
        rendered = template.render(Context({}))

        self.assertHTMLEqual(
            rendered,
            """
            <custom-template>
                <header>Override header</header>
                <main>Default main</main>
                <footer>Default footer</footer>
            </custom-template>
            <custom-template>
                <header>Default header</header>
                <main>Override main</main>
                <footer>Default footer</footer>
            </custom-template>
            <custom-template>
                <header>Default header</header>
                <main>Default main</main>
                <footer>Override footer</footer>
            </custom-template>
        """,
        )
