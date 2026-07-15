from fertility_popeve.burden.phenotype_exporter import (
    export_analysis_label_list,
)


def test_export_analysis_label_list(tmp_path):
    output = export_analysis_label_list(tmp_path)

    assert output.exists()

    text = output.read_text()

    assert "analysis.label" in text
    assert "EA" in text
    assert "NF" in text
    assert "GV" in text
    assert "MI" in text
