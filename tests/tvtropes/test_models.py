from app.models.tvtropes import TropeExample, EmbedTropeExample
import pandas as pd
import pytest

@pytest.fixture
def trope_examples_df():
    df = pd.DataFrame([{
        'Title': 'ABadCaseOfStripes',
        'title_id': 'lit0',
        'author': 'David Shannon',
        'verified_gender': 'male',
        'Example': " A Bad Case Of Stripes focuses on a girl named Camilla Cream changing shape or colour whenever something is suggested",
        'Trope': 'InvoluntaryShapeshifting',
        'trope_id': 't27289',
        'CleanTitle': 'abadcaseofstripes'
    }], columns=['Title', 'title_id', 'author', 'verified_gender', 'Example', 'Trope', 'trope_id', 'CleanTitle'])
    return df

def test_tvtropes_models(trope_examples_df):
    example = TropeExample(**trope_examples_df.iloc[0].to_dict())
    assert example.title == 'ABadCaseOfStripes'
    assert example.title_id == 'lit0'
    assert example.author == 'David Shannon'
    assert example.example == " A Bad Case Of Stripes focuses on a girl named Camilla Cream changing shape or colour whenever something is suggested"
    assert example.trope == 'InvoluntaryShapeshifting'
    assert example.trope_id == 't27289'
    assert example.clean_title == 'abadcaseofstripes'

    example = TropeExample(**trope_examples_df.iloc[0].to_dict())
    assert example.title == 'ABadCaseOfStripes'
    assert example.title_id == 'lit0'
    assert example.example == " A Bad Case Of Stripes focuses on a girl named Camilla Cream changing shape or colour whenever something is suggested"
    assert example.trope == 'InvoluntaryShapeshifting'
    assert example.trope_id == 't27289'

    example = EmbedTropeExample(**trope_examples_df.iloc[0].to_dict(), dense_rep=[0.1, 0.2, 0.3])
    assert example.title == 'ABadCaseOfStripes'
    assert example.title_id == 'lit0'
    assert example.example == " A Bad Case Of Stripes focuses on a girl named Camilla Cream changing shape or colour whenever something is suggested"
    assert example.trope == 'InvoluntaryShapeshifting'
    assert example.trope_id == 't27289'
    assert example.dense_rep == [0.1, 0.2, 0.3]

    
