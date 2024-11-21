from app.data.tvtropes.crud import TropeExamplesCRUD
import pytest
import pandas as pd

def test_load_from_csv():
    crud = TropeExamplesCRUD.load_from_csv('lit_tropes')
    assert crud.name == 'lit_tropes'
    assert isinstance(crud.df, pd.DataFrame)

def test_get_trope_examples_for_title_id():
    crud = TropeExamplesCRUD.load_from_csv('lit_tropes')
    title_id = 'lit11735'
    examples = crud.get_trope_examples_for_title_id(title_id)
    assert len(examples) > 0
    assert examples[0].title_id == title_id

def test_get_trope_examples_for_title_id_goodreads():
    crud = TropeExamplesCRUD.load_from_csv('lit_goodreads_match')
    title_id = 'lit11735'
    examples = crud.get_trope_examples_for_title_id(title_id)
    assert len(examples) > 0
    assert examples[0].title_id == title_id