"""Registry of PyRIT prompt converters, selectable per attack pack via
AttackPack.pyrit_converters. Text-only converters that ship with pyrit
itself — deliberately excludes:
  - audio/image/video/document converters (extra deps, out of this
    project's text-only scope): add_image_*, audio_*, image_*, qr_code,
    pdf, word_doc, azure_speech_*, transparency_attack (image_path in/out).
  - converters whose required config doesn't fit this registry's simple
    "one value" YAML shape: search_replace (pattern + replace), repeat_token
    (token + count), selective_text (wraps another converter + a selection
    strategy object), text_jailbreak (needs a TextJailBreak template object).

YAML accepts three shapes per entry:
  - a plain string for a converter that needs no parameters, e.g. "base64"
    (STATIC_CONVERTERS) or "denylist" (LLM_NO_PARAM_CONVERTERS, still needs
    an LLM but takes no extra value)
  - {name: value} for a converter that takes exactly one parameter and no
    LLM, e.g. {caesar: 3} (STATIC_PARAM_CONVERTERS)
  - {name: value} for a converter that takes exactly one parameter and an
    LLM, e.g. {translation: french} (LLM_CONVERTERS)
"""

from pyrit.converter import (
    ArabicPresentationFormConverter,
    ArabiziConverter,
    AsciiArtConverter,
    AtbashConverter,
    Base2048Converter,
    Base64Converter,
    BidiConverter,
    BinaryConverter,
    BinAsciiConverter,
    BrailleConverter,
    CaesarConverter,
    CharacterSpaceConverter,
    CharSwapConverter,
    CodeChameleonConverter,
    ColloquialWordswapConverter,
    DecompositionConverter,
    DenylistConverter,
    DiacriticConverter,
    EcojiConverter,
    EmojiConverter,
    FirstLetterConverter,
    FlipConverter,
    InsertPunctuationConverter,
    JsonStringConverter,
    LeetspeakConverter,
    MaliciousQuestionGeneratorConverter,
    MathObfuscationConverter,
    MathPromptConverter,
    MorseConverter,
    NatoConverter,
    NegationTrapConverter,
    PersuasionConverter,
    PolicyPuppetryConverter,
    RandomCapitalLettersConverter,
    RandomTranslationConverter,
    ROT13Converter,
    ScientificTranslationConverter,
    StringJoinConverter,
    SuffixAppendConverter,
    SuperscriptConverter,
    TaskFramingConverter,
    TatweelConverter,
    TemplateSegmentConverter,
    TenseConverter,
    ToneConverter,
    ToxicSentenceGeneratorConverter,
    TranslationConverter,
    UnicodeConfusableConverter,
    UnicodeReplacementConverter,
    UnicodeSubstitutionConverter,
    UrlConverter,
    VariationConverter,
    ZalgoConverter,
    ZeroWidthConverter,
)
from pyrit.prompt_normalizer import ConverterConfiguration
from pyrit.prompt_target import PromptTarget

# Plain string, zero-arg construction, no LLM involved.
STATIC_CONVERTERS = {
    "base64": Base64Converter,
    "rot13": ROT13Converter,
    "leetspeak": LeetspeakConverter,
    "morse": MorseConverter,
    "unicode_confusable": UnicodeConfusableConverter,
    "string_join": StringJoinConverter,
    "character_space": CharacterSpaceConverter,
    "ascii_art": AsciiArtConverter,
    "atbash": AtbashConverter,
    "binary": BinaryConverter,
    "bin_ascii": BinAsciiConverter,
    "braille": BrailleConverter,
    "charswap": CharSwapConverter,
    "colloquial_wordswap": ColloquialWordswapConverter,
    "diacritic": DiacriticConverter,
    "ecoji": EcojiConverter,
    "emoji": EmojiConverter,
    "first_letter": FirstLetterConverter,
    "flip": FlipConverter,
    "insert_punctuation": InsertPunctuationConverter,
    "json_string": JsonStringConverter,
    "math_obfuscation": MathObfuscationConverter,
    "nato": NatoConverter,
    "negation_trap": NegationTrapConverter,
    "policy_puppetry": PolicyPuppetryConverter,
    "random_capital_letters": RandomCapitalLettersConverter,
    "superscript": SuperscriptConverter,
    "task_framing": TaskFramingConverter,
    "tatweel": TatweelConverter,
    "template_segment": TemplateSegmentConverter,
    "unicode_replacement": UnicodeReplacementConverter,
    "unicode_sub": UnicodeSubstitutionConverter,
    "url": UrlConverter,
    "zalgo": ZalgoConverter,
    "zero_width": ZeroWidthConverter,
    "arabizi": ArabiziConverter,
    "arabic_presentation_form": ArabicPresentationFormConverter,
    "bidi": BidiConverter,
    "base2048": Base2048Converter,
}

# {name: value}, single required parameter, no LLM involved.
STATIC_PARAM_CONVERTERS = {
    "caesar": lambda value: CaesarConverter(caesar_offset=int(value)),
    "suffix_append": lambda value: SuffixAppendConverter(suffix=value),
    # encrypt_type: one of "reverse", "binary_tree", "odd_even", "length" — "custom" needs
    # Python callables, which don't fit a YAML value, so it's out of scope here.
    "codechameleon": lambda value: CodeChameleonConverter(encrypt_type=value),
}

# Plain string, needs an LLM target but no extra parameter.
LLM_NO_PARAM_CONVERTERS = {
    "denylist": lambda target: DenylistConverter(converter_target=target),
    "malicious_question_generator": lambda target: MaliciousQuestionGeneratorConverter(converter_target=target),
    "math_prompt": lambda target: MathPromptConverter(converter_target=target),
    "variation": lambda target: VariationConverter(converter_target=target),
    "toxic_sentence_generator": lambda target: ToxicSentenceGeneratorConverter(converter_target=target),
    "decomposition": lambda target: DecompositionConverter(converter_target=target),
    "random_translation": lambda target: RandomTranslationConverter(converter_target=target),
}

# {name: value}, single required parameter, needs an LLM target.
LLM_CONVERTERS = {
    "translation": lambda target, value: TranslationConverter(converter_target=target, language=value),
    "tone": lambda target, value: ToneConverter(converter_target=target, tone=value),
    "tense": lambda target, value: TenseConverter(converter_target=target, tense=value),
    "persuasion": lambda target, value: PersuasionConverter(converter_target=target, persuasion_technique=value),
    "scientific_translation": lambda target, value: ScientificTranslationConverter(
        converter_target=target, mode=value
    ),
}


def build_converters(names: list[str | dict[str, str]], *, llm_target: PromptTarget) -> list:
    converters = []
    for entry in names:
        if isinstance(entry, str):
            if entry in STATIC_CONVERTERS:
                converters.append(STATIC_CONVERTERS[entry]())
            elif entry in LLM_NO_PARAM_CONVERTERS:
                converters.append(LLM_NO_PARAM_CONVERTERS[entry](llm_target))
            else:
                raise ValueError(
                    f"Unknown pyrit_converters entry {entry!r}. Known no-parameter converters: "
                    f"{list(STATIC_CONVERTERS) + list(LLM_NO_PARAM_CONVERTERS)}"
                )
        else:
            (name, value), = entry.items()
            if name in STATIC_PARAM_CONVERTERS:
                converters.append(STATIC_PARAM_CONVERTERS[name](value))
            elif name in LLM_CONVERTERS:
                converters.append(LLM_CONVERTERS[name](llm_target, value))
            else:
                raise ValueError(
                    f"Unknown pyrit_converters entry {name!r}. Known parameterized converters: "
                    f"{list(STATIC_PARAM_CONVERTERS) + list(LLM_CONVERTERS)}"
                )
    return converters


def to_converter_configuration(converters: list) -> list[ConverterConfiguration]:
    return ConverterConfiguration.from_converters(converters=converters)
