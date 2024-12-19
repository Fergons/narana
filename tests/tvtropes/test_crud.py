from app.crud.tvtropes import TropeExamplesCRUD
from app.models.tvtropes import TropeExample
import pytest
import pandas as pd

@pytest.fixture
def goodreads_CRUD():
    df = pd.DataFrame([{
        'Title': 'ABadCaseOfStripes',
        'title_id': 'lit0',
        'author': 'David Shannon',
        'verified_gender': 'male',
        'Example': " A Bad Case Of Stripes focuses on a girl named Camilla Cream changing shape or colour whenever something is suggested.",
        'Trope': 'InvoluntaryShapeshifting',
        'trope_id': 't27289',
        'CleanTitle': 'abadcaseofstripes'
    }], columns=['Title', 'title_id', 'author', 'verified_gender', 'Example', 'Trope', 'trope_id', 'CleanTitle'])
    return TropeExamplesCRUD(df=df, name='lit_goodreads')


@pytest.fixture
def lit_CRUD():
    df = pd.DataFrame([{
        'Title': 'ABadCaseOfStripes',
        'title_id': 'lit0',
        'Example': " A Bad Case Of Stripes focuses on a girl named Camilla Cream changing shape or colour whenever something is suggested.",
        'Trope': 'InvoluntaryShapeshifting',
        'trope_id': 't27289'
    }], columns=['Title', 'title_id', 'Example', 'Trope', 'trope_id'])
    return TropeExamplesCRUD(df=df, name='lit_tropes')




def test_load_from_csv():
    crud = TropeExamplesCRUD.load_from_csv('lit_tropes')
    assert isinstance(crud.df, pd.DataFrame)
    assert crud.name == 'lit_tropes'

def test_get_trope_examples_for_title_id(lit_CRUD):
    crud = lit_CRUD
    title_id = 'lit0'
    examples = crud.get_trope_examples_for_title_id(title_id)
    assert len(examples) > 0
    assert examples[0].title_id == title_id

    title_id = 'lit1'
    examples = crud.get_trope_examples_for_title_id(title_id)
    assert len(examples) == 0

def test_get_trope_examples_for_title_id_goodreads(goodreads_CRUD):
    crud = goodreads_CRUD
    title_id = 'lit0'
    examples = crud.get_trope_examples_for_title_id(title_id)
    assert len(examples) > 0
    assert examples[0].title_id == title_id
    assert examples[0].clean_title is not None

    title_id = 'lit1'
    examples = crud.get_trope_examples_for_title_id(title_id)
    assert len(examples) == 0


def test_get_titles(goodreads_CRUD):
    crud = goodreads_CRUD
    titles = crud.get_titles(limit=2, offset=0)
    assert len(titles) == 1
    titles = crud.get_titles(limit=1, offset=1)
    assert len(titles) == 0
