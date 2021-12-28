"""Test the edit functions to apply changes."""
from lawinprogress.apply_changes.edit_functions import (
    __clean_text,
    __split_text_to_sentences,
    _append,
    _cancelled,
    _delete_after,
    _insert_after,
    _rephrase,
    _replace,
)
from lawinprogress.parsing.lawtree import LawTextNode
from lawinprogress.parsing.parse_change_law import Change


def test_clean_text():
    """Test if text is properly cleaned."""
    test_text = "This is  a test   text with whitespaces."
    clean_text = __clean_text(test_text)

    assert clean_text == "This is a test text with whitespaces."


def test_split_text_to_sentences_hard_sentences():
    """Test if hard multi-sentence text is properly split."""
    test_text = """Auch für Aufgrabungen und Baumaßnahmen der Versorgungsunternehmen im  Zusammenhang  mit  Maßnahmen  nach  den  Absätzen  5  und  6  bedarf  es  der  straßenrechtlichen  Erlaubnis.  Notfälle,  in  denen  sofortiges  Handeln  zur  Schadensabwehr geboten ist, sind der Straßenbaubehörde und, soweit Flächen für  den Fahrzeugverkehr im übergeordneten Straßennetz betroffen sind, auch der für  Verkehr zuständigen Senatsverwaltung anzuzeigen; die Einholung der Erlaubnis nach  Satz  1  ist  unverzüglich  nachzuholen.  Aufgrabungen  und  Baumaßnahmen  mit  unwesentlicher Beeinträchtigung des Gemeingebrauchs sind, soweit Flächen für den  Fahrzeugverkehr  im  übergeordneten  Straßennetz  nicht  betroffen  sind,  der  Straßenbaubehörde  abweichend  von  Satz  1  nur  anzuzeigen;  die  Einholung  der  Erlaubnis nach Satz 1 ist unverzüglich nachzuholen, sobald erkennbar ist, dass sich  die  Beeinträchtigung  über  das  unwesentliche  Maß  hinaus  ausweiten  wird.  Eine  Sicherheitsleistung  darf  nur  verlangt  werden,  soweit  dies  zur  Sicherung  einer  ordnungsgemäßen Wiederherstellung der Straße erforderlich ist."""
    sentences = __split_text_to_sentences(test_text)

    assert len(sentences) == 6


def test_split_text_to_sentences_simple_sentences():
    """Test if basic multi-sentence text is properly split."""
    test_text = "This is a sentence. This is another sentence."
    sentences = __split_text_to_sentences(test_text)

    assert len(sentences) == 2
    assert sentences[0] == "This is a sentence."
    assert sentences[1] == "This is another sentence."


def test_split_text_to_sentences_one_sentence():
    """Test if a sentence text is properly preserved."""
    test_text = "This is only one sentence."
    sentences = __split_text_to_sentences(test_text)

    assert len(sentences) == 1
    assert sentences[0] == "This is only one sentence."


def test_replace_success():
    """Test if text in a node can be replaced properly."""
    node = LawTextNode(bulletpoint="(1)", text="Test text to replace;")
    change = Change(
        location="(1)",
        sentences=[],
        text=["text to replace", "replaced"],
        change_type="replace",
        raw_text="(1) - Replace something in this test.",
    )

    res = _replace(node, change)

    assert res.status == 1
    assert node.text == "Test replaced;"


def test_replace_failure():
    """Test if replace fails as expected."""
    node = LawTextNode(bulletpoint="(1)", text="Test text to replace;")
    change = Change(
        location="(1)",
        sentences=[],
        text=["text to replace"],
        change_type="replace",
        raw_text="(1) - Replace some text, this is a test.",
    )

    res = _replace(node, change)

    assert res.status == 0
    assert node.text == "Test text to replace;"


def test_insert_after_with_paired_texts():
    """Test if insert_after works fine if the text comes in pairs (location, text_to_insert)."""
    node = LawTextNode(bulletpoint="(1)", text="Test text insert here;")
    change = Change(
        location="(1)",
        sentences=[],
        text=["insert", "inserted"],
        change_type="insert_after",
        raw_text="(1) - Insert some text, this is a test.",
    )

    res = _insert_after(node, change)

    assert res.status == 1
    assert node.text == "Test text insert inserted here;"


def test_insert_after_bulletpointmatch_exists():
    """Test if insert_after works fine if a bulletpoint match with one text happens and the node already exists in the tree."""
    parent_node = LawTextNode(bulletpoint="§ 1", text="Test parent node")
    node = LawTextNode(
        bulletpoint="(1)", text="Test text insert here;", parent=parent_node
    )
    change = Change(
        location="(1)",
        sentences=[],
        text=["(1) New inserted node text"],
        change_type="insert_after",
        raw_text="(1) - Insert some text, this is a test.",
    )

    res = _insert_after(node, change)

    assert res.status == 1
    assert len(parent_node.children) == 2
    assert node.text == "Test text insert here;"
    assert node.bulletpoint == "(2)"
    assert parent_node.children[0].bulletpoint == "(1)"
    assert parent_node.children[0].text == "New inserted node text"


def test_insert_after_bulletpointmatch_doesnt_exist():
    """Test if insert_after works fine if a bulletpoint match with one text happens and the node doesnt exists in the tree."""
    parent_node = LawTextNode(bulletpoint="§ 1", text="Test parent node")
    node = LawTextNode(
        bulletpoint="(1)", text="Test text insert here;", parent=parent_node
    )
    change = Change(
        location="(1)",
        sentences=[],
        text=["(2) New inserted node text"],
        change_type="insert_after",
        raw_text="(1) - Insert something in this test.",
    )

    res = _insert_after(node, change)

    assert res.status == 1
    assert len(parent_node.children) == 2
    assert node.text == "Test text insert here;"
    assert node.bulletpoint == "(1)"
    assert parent_node.children[1].bulletpoint == "(2)"
    assert parent_node.children[1].text == "New inserted node text"


def test_insert_after_with_paired_texts():
    """Test if insert_after works fine with one text and a sentence specified."""
    node = LawTextNode(
        bulletpoint="(1)",
        text="Test text insert after this sentence. And before this sentence.",
    )
    change = Change(
        location="(1)",
        sentences=["nach Satz 1"],
        text=["Inserted sentence."],
        change_type="insert_after",
        raw_text="(1) - Insert some text, this is a test.",
    )

    res = _insert_after(node, change)

    assert res.status == 1
    assert (
        node.text
        == "Test text insert after this sentence. Inserted sentence. And before this sentence."
    )


def test_insert_after_fails_with_no_text():
    """Test if insert_after fails if no text is given."""
    node = LawTextNode(bulletpoint="(1)", text="Test text to replace;")
    change = Change(
        location="(1)",
        sentences=[],
        text=[],
        change_type="insert_after",
        raw_text="(1) - ",
    )

    res = _insert_after(node, change)

    assert res.status == 0


def test_rephrase_with_one_text_no_sentence():
    """Test if rephrasing works with one text and no sentences given."""
    node = LawTextNode(bulletpoint="(1)", text="Text to rephrase in this sentence.")
    change = Change(
        location="(1)",
        sentences=[],
        text=["(1) Rephrased text."],
        change_type="rephrase",
        raw_text="(1) - Rephrase some text, this is a test.",
    )

    res = _rephrase(node, change)

    assert res.status == 1
    assert node.text == "Rephrased text."


def test_rephrase_with_one_text_one_sentence():
    """Test if rephrasing works with one text and one sentences given."""
    node = LawTextNode(
        bulletpoint="(1)",
        text="Here is nothing to do. Text to rephrase in this sentence.",
    )
    change = Change(
        location="(1)",
        sentences=["Satz 2"],
        text=["Text to rephrase."],
        change_type="rephrase",
        raw_text="(1) - Rephrase some text, this is a test.",
    )

    res = _rephrase(node, change)

    assert res.status == 1
    assert node.text == "Here is nothing to do. Text to rephrase."


def test_rephrase_fails_without_text():
    """Test if rephrasing fails without text given."""
    node = LawTextNode(
        bulletpoint="(1)",
        text="Here is nothing to do. Text to rephrase in this sentence.",
    )
    change = Change(
        location="(1)",
        sentences=[],
        text=[],
        change_type="rephrase",
        raw_text="(1) - Rephrase some text, this is a test.",
    )

    res = _rephrase(node, change)

    assert res.status == 0
    assert node.text == "Here is nothing to do. Text to rephrase in this sentence."


def test_append_success_one_text():
    """Test if appending the text to a specific location works."""
    node = LawTextNode(bulletpoint="(1)", text="Current text to append to.")
    change = Change(
        location="(1)",
        sentences=[],
        text=["Appended text."],
        change_type="append",
        raw_text="(1) - Append some text, this is a test.",
    )

    res = _append(node, change)

    assert res.status == 1
    assert node.text == "Current text to append to. Appended text."


def test_append_fails_too_much_texts():
    """Test if appending fails with too much text."""
    node = LawTextNode(bulletpoint="(1)", text="Current text to append to.")
    change = Change(
        location="(1)",
        sentences=[],
        text=["Appended text.", "More text"],
        change_type="append",
        raw_text="(1) - Append some text, this is a test.",
    )

    res = _append(node, change)

    assert res.status == 0
    assert node.text == "Current text to append to."


def test_append_fails_too_little_texts():
    """Test if appending fails with too little text."""
    node = LawTextNode(bulletpoint="(1)", text="Current text to append to.")
    change = Change(
        location="(1)",
        sentences=[],
        text=[],
        change_type="append",
        raw_text="(1) - Append some text, this is a test.",
    )

    res = _append(node, change)

    assert res.status == 0
    assert node.text == "Current text to append to."


def test_delete_after_one_text():
    """Test if deleting a specific text works."""
    node = LawTextNode(bulletpoint="(1)", text="Current to delete text.")
    change = Change(
        location="(1)",
        sentences=[],
        text=["to delete"],
        change_type="delete_after",
        raw_text="(1) - Delete some text, this is a test.",
    )

    res = _delete_after(node, change)

    assert res.status == 1
    assert node.text == "Current text."


def test_delete_after_two_texts():
    """Test if deleting after a specific text works."""
    node = LawTextNode(bulletpoint="(1)", text="Current to delete text.")
    change = Change(
        location="(1)",
        sentences=[],
        text=["to delete", "text"],
        change_type="delete_after",
        raw_text="(1) - Delete some text, this is a test.",
    )

    res = _delete_after(node, change)

    assert res.status == 1
    assert node.text == "Current to delete ."


def test_delete_after_fails_without_text():
    """Test if deleting after fails without text given."""
    node = LawTextNode(bulletpoint="(1)", text="Current to delete text.")
    change = Change(
        location="(1)",
        sentences=[],
        text=[],
        change_type="delete_after",
        raw_text="(1) - Delete some text, this is a test.",
    )

    res = _delete_after(node, change)

    assert res.status == 0
    assert node.text == "Current to delete text."


def test_cancelled_remove_node():
    """Test if cancelling a node works."""
    parent_node = LawTextNode(bulletpoint="§ 1", text="Test parent node")
    node = LawTextNode(bulletpoint="(1)", text="Node to remove.", parent=parent_node)
    other_node = LawTextNode(
        bulletpoint="(2)", text="Node to remain.", parent=parent_node
    )
    change = Change(
        location="(1)",
        sentences=[],
        text=[],
        change_type="cancelled",
        raw_text="(1) - Cancel some text, this is a test.",
    )

    res = _cancelled(node, change)

    assert res.status == 1
    assert len(parent_node.children) == 1
    assert other_node.bulletpoint == "(1)"
    assert other_node.text == "Node to remain."
