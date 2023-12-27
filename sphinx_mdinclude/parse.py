import re
from typing import Any, Dict, Match, Tuple

from mistune import BlockParser, InlineParser
from mistune.inline_parser import HTML_ATTRIBUTES, HTML_TAGNAME


State = Dict[str, Any]
Token = Dict[str, Any]
Element = Tuple[str, ...]


class RestBlockParser(BlockParser):
    DIRECTIVE = re.compile(
        r"^( *\.\..*?)\n(?=\S)",
        re.DOTALL | re.MULTILINE,
    )
    ONELINE_DIRECTIVE = re.compile(
        r"^( *\.\..*?)$",
        re.DOTALL | re.MULTILINE,
    )
    REST_CODE_BLOCK = re.compile(
        r"^::\s*$",
        re.DOTALL | re.MULTILINE,
    )

    SPECIFICATION = BlockParser.SPECIFICATION.copy()
    SPECIFICATION.update({
        "directive": DIRECTIVE,
        "oneline_directive": ONELINE_DIRECTIVE,
        "rest_code_block": REST_CODE_BLOCK,
    })

    DEFAULT_RULES = BlockParser.DEFAULT_RULES + (
        "directive",
        "oneline_directive",
        "rest_code_block",
    )

    def parse_directive(self, match: Match, state: State) -> Token:
        return {"type": "directive", "text": match.group(1)}

    def parse_oneline_directive(self, match: Match, state: State) -> Token:
        # reuse directive output
        return {"type": "directive", "text": match.group(1)}

    def parse_rest_code_block(self, match: Match, state: State) -> Token:
        return {"type": "rest_code_block", "text": ""}


class RestInlineParser(InlineParser):
    REST_ROLE = r":.*?:`.*?`|`[^`]+`:.*?:"
    REST_LINK = r"`[^`]*?`_"
    INLINE_MATH = r"`\$((.*?)\$`)"
    EOL_LITERAL_MARKER = r"(\s+)?::\s*$"

    # add colon and space as special text
    TEXT = r"^[\s\S]+?(?=[\\<!\[:_*`~ ]|https?://| {2,}\n|$)"

    # __word__ or **word**
    DOUBLE_EMPHASIS = r"^([_*]){2}(?P<text>[\s\S]+?)\1{2}(?!\1)"
    # _word_ or *word*
    EMPHASIS = (
        r"^\b_((?:__|[^_])+?)_\b",  # _word_
        r"^\*(?P<text>(?:\*\*|[^\*])+?)\*(?!\*)",  # *word*
    )

    # make inline_html span open/contents/close instead of just a single tag
    INLINE_HTML = (
        r"(?<!\\)<" + HTML_TAGNAME + HTML_ATTRIBUTES + r"\s*>"  # open tag
        r"(.*)"
        r"(?<!\\)</" + HTML_TAGNAME + r"\s*>|"  # close tag
        r"(?<!\\)<" + HTML_TAGNAME + HTML_ATTRIBUTES + r"\s*/>|"  # open/close tag
        r"(?<!\\)<\?[\s\S]+?\?>|"
        r"(?<!\\)<![A-Z][\s\S]+?>|"  # doctype
        r"(?<!\\)<!\[CDATA[\s\S]+?\]\]>"  # cdata
    )

    SPECIFICATION = InlineParser.SPECIFICATION.copy()
    SPECIFICATION.update({
        "inline_math": INLINE_MATH,
        "rest_link": REST_LINK,
        "rest_role": REST_ROLE,
        "eol_literal_marker": EOL_LITERAL_MARKER,
        "inline_html": INLINE_HTML,
    })

    DEFAULT_RULES = (
        "inline_math",
        # "image_link",
        "rest_role",
        "rest_link",
        "eol_literal_marker",
    ) + InlineParser.DEFAULT_RULES

    def parse_double_emphasis(self, match: Match, state: State) -> Element:
        # may include code span
        return "double_emphasis", match.group("text")

    def parse_emphasis(self, match: Match, state: State) -> Element:
        # may include code span
        return "emphasis", match.group("text") or match.group(1)

    def parse_image_link(self, match: Match, state: State) -> Element:
        """Pass through rest role."""
        alt, src, target = match.groups()
        return "image_link", src, target, alt

    def parse_rest_role(self, match: Match, state: State) -> Element:
        """Pass through rest role."""
        return "rest_role", match.group(0)

    def parse_rest_link(self, match: Match, state: State) -> Element:
        """Pass through rest link."""
        return "rest_link", match.group(0)

    def parse_inline_math(self, match: Match, state: State) -> Element:
        """Pass through rest link."""
        return "inline_math", match.group(2)

    def parse_eol_literal_marker(self, match: Match, state: State) -> Element:
        """Pass through rest link."""
        marker = ":" if match.group(1) is None else ""
        return "eol_literal_marker", marker
