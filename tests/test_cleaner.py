from leggitutto.cleaner import (finalize, is_page_number, join_lines, normalize_chars, reflow_plain_text,
                                remove_note_markers, remove_running_heads, strip_toc_leaders)
from leggitutto.model import Extracted, Para
from leggitutto.settings import Options


def test_page_numbers():
    for text in ["12", "- 12 -", "[3]", "Pagina 4", "pag. 7", "Page 3 of 10", "5 / 120", "xiv", "Pagina 2 di 9"]:
        assert is_page_number(text), text
    for text in ["1984 fu un anno", "Capitolo 3", "Roma", "I"]:
        assert not is_page_number(text), text


def test_hyphenation_and_join():
    assert join_lines(["Questo è un proble-", "ma serio"]) == "Questo è un problema serio"
    assert join_lines(["Emilia-", "Romagna"]) == "Emilia-Romagna"
    assert join_lines(["una riga", "e l'altra"]) == "una riga e l'altra"


def test_note_markers():
    assert remove_note_markers("parola¹ e altra²³.") == "parola e altra."
    assert remove_note_markers("come detto[12], poi") == "come detto, poi"
    assert remove_note_markers("una stanza di 20 m² circa") == "una stanza di 20 m² circa"


def test_invisible_characters_and_ligatures():
    assert normalize_chars("eﬃcace­​") == "efficace"
    assert normalize_chars(" voce") == "• voce"


def test_toc_leaders():
    assert strip_toc_leaders("Capitolo primo ........ 12") == "Capitolo primo"


def test_running_heads_removed():
    pages = [[Para("Il mio libro", zone="top"), Para(f"Testo della pagina {i}."), Para(str(i), zone="bottom")] for i in range(1, 6)]
    text = finalize(Extracted(pages=pages), Options())
    assert "Il mio libro" not in text
    assert "Testo della pagina 3." in text
    assert "\n3\n" not in text


def test_paragraph_across_pages_is_joined():
    pages = [[Para("La frase continua")], [Para("sulla pagina dopo.")]]
    assert finalize(Extracted(pages=pages), Options()).strip() == "La frase continua sulla pagina dopo."


def test_reflow_hard_wrapped_text():
    line = "Questa è una riga di testo abbastanza lunga da sembrare spezzata a mano e"
    text = "\n".join([line] * 6) + "\nfine.\n\nAltro paragrafo."
    paras = reflow_plain_text(text)
    assert len(paras) == 2
    assert paras[0].text.endswith("e fine.")


def test_keep_everything_option():
    opts = Options(remove_page_numbers=False)
    pages = [[Para("Testo."), Para("7", zone="bottom")]]
    assert "7" in finalize(Extracted(pages=pages), opts)


def test_running_heads_needs_repetition():
    pages = [[Para("Titolo unico", zone="top"), Para("Testo.")]]
    assert remove_running_heads(pages) == pages
