"""Pipeline markdown → HTML.

Es un único pipeline: se usa al guardar una entrada (el HTML se cachea en
posts.content_html) y lo usará también el preview del editor (Fase 4), así
el preview siempre coincide con el resultado publicado.

- Código: bloques ``` resaltados con Pygments (clases CSS, ver pygments.css),
  con números de línea (spans .linenos, no seleccionables al copiar).
- Math: $...$ y $$...$$ se preservan intactos (markdown no los toca) y se
  emiten como \\(...\\) y \\[...\\] para que KaTeX los renderice en el cliente.
- Raw HTML permitido (p. ej. <video>, iframes de YouTube): es seguro porque
  solo el admin escribe entradas.
"""

from html import escape

from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin
from pygments import highlight as pygments_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

# linenos="inline": cada línea va precedida de un <span class="linenos">N</span>
_formatter = HtmlFormatter(linenos="inline")

# Pygments envuelve su salida en este div; lo quitamos para quedarnos solo con
# el <pre>: markdown-it usa el resultado tal cual cuando empieza con "<pre"
_WRAPPER_PREFIX = '<div class="highlight">'
_WRAPPER_SUFFIX = "</div>\n"


def _highlight(code: str, lang: str, attrs: str) -> str:
    """Resalta un bloque de código con números de línea.

    Si el lenguaje no se reconoce (o no se indicó), se usa el lexer de texto
    plano: sin colores pero con números de línea igual.
    """
    try:
        lexer = get_lexer_by_name(lang) if lang else TextLexer()
    except ClassNotFound:
        lexer = TextLexer()

    html = pygments_highlight(code, lexer, _formatter)
    if html.startswith(_WRAPPER_PREFIX) and html.endswith(_WRAPPER_SUFFIX):
        html = html[len(_WRAPPER_PREFIX):-len(_WRAPPER_SUFFIX)]
    return html


def _math_inline(self, tokens, idx, options, env):
    return f"\\({escape(tokens[idx].content)}\\)"


def _math_block(self, tokens, idx, options, env):
    return f'<div class="math-block">\\[{escape(tokens[idx].content)}\\]</div>\n'


_md = MarkdownIt("commonmark", {"html": True, "highlight": _highlight})
_md.enable(["table", "strikethrough"])
# double_inline: $$...$$ dentro de un párrafo también cuenta como bloque display
_md.use(dollarmath_plugin, allow_labels=False, double_inline=True)
_md.add_render_rule("math_inline", _math_inline)
_md.add_render_rule("math_inline_double", _math_block)
_md.add_render_rule("math_block", _math_block)


def render_markdown(text: str) -> str:
    return _md.render(text)
