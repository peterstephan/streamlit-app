# Import dependencies
import streamlit as st
import yaml
import pandas as pd
import numpy as np
import time
import io
import xlsxwriter
import os


# Page Config #
st.set_page_config(
    page_title = "MCA Tool",
    page_icon = "🚴"
    )

#Set the page max width
def _max_width_():
    max_width_str = f"max-width: 1200px;"
    st.markdown(
        f"""
    <style>
    .appview-container .main .block-container{{
        {max_width_str}
    }}
    </style>    
    """,
        unsafe_allow_html=True,
    )
_max_width_()

# Import data from input files
for filename in ('inputs', 'variables', 'NOF_solutions'):
    with open('%s.yaml' % filename) as file:
        Inpt_lst = yaml.load(file, Loader=yaml.FullLoader)
        for key, dcts in Inpt_lst.items():
            for i, dct in enumerate(dcts):
                db = pd.DataFrame.from_dict(dct, orient='index').transpose()
                if i == 0:
                    globals()[key] = db
                else:
                    globals()[key]  = globals()[key] .append(db)
            globals()[key] .index = np.arange(1, len(globals()[key])+1)
criteria_category = dict(zip(CriteriaList.Criterion, CriteriaList.Category))


#### Introduction ####
st.header("Smarter Solutions")
st.subheader("Multi-Criteria Analysis (MCA) Tool")
st.write('''This Smarter Solutions Multi-Criteria Analysis **(MCA)** Tool provides a clear line-of-sight across the Department of Transport and Main Roads' **(TMR)** infrastructure planning and investment process, providing assurance that the Network Optimisation Framework is embedded in our decision-making.
    The MCA Tool has been designed for use in selecting a preferred option, or ranking alternate options, where network optimisation solutions **(NOS)** are included within assessment processes. The MCA Tool applies a standardised consideration of NOS relative to large capital infrastructure, ensuring TMR is delivering the right infrastructure at the right time and aligning with government policy direction for investment as outlined in the Queensland Government's State Infrastructure Plan.
''')

#### Project Description ####
with st.expander("Project Description", expanded=True):
    if st.button("Help", key=1):
        st.sidebar.write("Help with Project Description")
    st.write('''The project must be clearly defined within the MCA to ensure that appropriate options are short-listed for evaluation and that the criteria selected for assessment reflect the nature of the service requirement or opportunity. Accordingly, the project should be defined in terms of:''')
    answers = []     
    for _, row in ProjectDescription.iterrows():
        st.write('%s:' % row.Category)
        if row.hasnans: 
            answers.append(st.text_input(row.Question))
        else:
            answers.append(','.join([x for x in st.multiselect(row.Question, row.Options)]))
    ProjectDescription['answers'] = answers
ProjectDescription = ProjectDescription[['Category', 'answers']]

with st.expander('Import data from previously saved Excel file:', expanded=True):
    uploaded_project = st.file_uploader('Upload Saved Project',type='xlsx')
    if uploaded_project is not None:
        UserInputs = pd.read_excel (uploaded_project, sheet_name='UserInputs')
        st.markdown('You uploaded a file successfully.')
    else:
        UserInputs = pd.DataFrame(columns=['Criterion','Ranks'])
    UserInputs.set_index('Criterion', inplace=True)

#### NOF Options #### 
# New section that asks the General User to complete a preliminary review of the 
# application of each NOF option (Yes/No) in the Smarter Solutions Reference Guide 
# to determine which option should be included in the rest of the MCA process. 
with st.expander("Define Options", expanded=True):
    if st.button("Help", key=2):
        st.sidebar.write("Help with Define Options")
    st.write('Choose from NOF options bla bla.')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader('Relevant Option?')
    with col2:
        st.subheader('NOF Solution')
    with col3:
        st.subheader('')
    NOFsolutions = NOFsolutions[NOFsolutions.Solution.apply(lambda x: x not in UserInputs.columns)]
    for itr, option in NOFsolutions.iterrows():
        col1, col2, col3 = st.columns(3)
        with col1:
            chck = st.checkbox('', key='NOFsolutions_ch%s' % itr)
        with col2:
            st.markdown(option.Solution)
        if chck:
            with col3:
                Comment = st.text_input('Comment on the solution: %s' % option.Solution, option.Comment, key='NOFsolutions_cm%s' % option.Solution)
            UserInputs[option.Solution] = [3] * len(UserInputs)
    while True:
        col1, col2 = st.columns(2)
        with col1:
            itr = len(UserInputs.columns)
            new_option = st.text_input('What is option %i?' % itr, 'Add new option', key='new_option%i' % itr)
        with col2:
            new_option_comment = st.text_area('Option description', 'Add new option', key='new_option_comment%i' % itr)
        if 'Add new option' in (new_option, new_option_comment):
            break
        else:
            UserInputs[new_option] = [3] * len(UserInputs)

#### Criteria ####
with st.expander("Criteria", expanded=True):
    if st.button("Help", key=3):
        st.sidebar.write("Help with Criteria")
    st.write('''As per the Smarter solutions -  Multi-Criteria Assessment Technical Note, various criteria are mandatory when considering an NOS in the evaluation process. Additional criteria relating to intersection delay, public transport patronage and freight should be selected where appropriate. ''')
    st.dataframe(CriteriaList)
    NewCriteria = CriteriaList.copy()
    NewCriteria = NewCriteria[NewCriteria.Criterion.apply(lambda x: x not in UserInputs.index)]
    nos_flag = st.checkbox(''' Include all NOS Option's criteria''')
    nos_defaults = NewCriteria.loc[NewCriteria['NOS mandatory'] == True].index if nos_flag else ''
    SelectedRows = st.multiselect('Select rows:', NewCriteria.index, default=[x for x in nos_defaults])
    SelectedCriteria = NewCriteria.loc[SelectedRows].sort_index()
    for new_criterion in SelectedCriteria.iloc[:, 1]:
        UserInputs.loc[new_criterion] = [len(UserInputs) + 1] + [3] * (len(UserInputs.columns)-1)
    SelectedCriteria = CriteriaList.copy()
    SelectedCriteria = SelectedCriteria[SelectedCriteria.Criterion.apply(lambda x: x in UserInputs.index)]
    st.write('### Selected Criteria', SelectedCriteria)

#### Weightings Ranking ####
#### Scoring ####
AvailableRanks = list(range(1,len(UserInputs) + 1))
for Criterion, row in UserInputs.iterrows():
    with st.expander("Category: %s & criterion: %s" % (criteria_category[Criterion], Criterion)):
        label = 'Rank - criterion: %s' % Criterion
        index = AvailableRanks.index(row.Ranks) if row.Ranks in AvailableRanks else 0
        UserInputs.at[Criterion, 'Ranks'] = st.selectbox(label, AvailableRanks, index, key='rank_%s' % Criterion)
        for OptionName in UserInputs.columns[1:]:
            value = UserInputs.at[Criterion, OptionName]
            key = 'scores_%s_%s' % (Criterion, OptionName)
            UserInputs.at[Criterion, OptionName] = st.select_slider('Score - option: %s' %  OptionName, range(1,6), key=key, value=value)
    used = int(np.where(UserInputs.index.to_numpy() == Criterion)[0])
    AvailableRanks = [x for x in AvailableRanks if x not in list(UserInputs.Ranks.to_numpy())[:used+1]]

RankSums = [len(UserInputs) - x + 1 for x in UserInputs.Ranks]
RankSums_ttl = sum(RankSums)
RankSums = [x / RankSums_ttl for x in RankSums]
RankSums = np.array(RankSums)[:, np.newaxis]
options = list(UserInputs.columns[1:])
if len(UserInputs.columns) > 2 and len(UserInputs) > 1:
    UserScores = UserInputs.iloc[:, 1:].to_numpy()
    # to add the base case with score 3
    Scores = np.c_[np.ones(len(UserScores))+2, UserScores]
    Scores *= RankSums
    st.write('Summary of Option Scoring:')
    ScoresTotal = Scores.sum(axis=0)
    OverallScore = pd.DataFrame(ScoresTotal)
    OverallScore = OverallScore.transpose()
    OverallScore.columns = ['Base Case'] + options
    OverallScore['title'] = 'Score'
    OverallScore.set_index('title', inplace=True)
    OverallScore = OverallScore.transpose()
    OverallScore

    # Summary of Option Rankings
    st.write('Summary of Option Rankings:')
    tmp = (-ScoresTotal).argsort()
    FinalRanks = np.empty_like(tmp)
    FinalRanks[tmp] = np.arange(len(ScoresTotal))
    FinalRanks += 1
    OverallRank = pd.DataFrame(FinalRanks)
    OverallRank = OverallRank.transpose()
    OverallRank.columns = ['Base Case'] + options
    OverallRank['title'] = 'Rank'
    OverallRank.set_index('title', inplace=True)
    OverallRank = OverallRank.transpose()
    OverallRank.sort_values(['Rank'])
    OverallRank

    # Best Option
    st.header('Best Option:')
    st.subheader('Overall: \n%s' % OverallRank.index[np.where(FinalRanks==1)][0])
    scores_by_criteria = SelectedCriteria.copy()
    for j, y in enumerate(options):
        scores_by_criteria['Score_%s' % y] = [Scores[i, j + 1] / UserInputs.Ranks[i] for i in range(len(Scores))] # j + 1 instead of j to exclude BASE
    scores_by_criteria['Category'] = [criteria_category[x] for x in UserInputs.index]
    scores_by_category = scores_by_criteria.groupby('Category').sum()[['Score_%s' % y for y in options]]
    scores_by_category.columns = [x[6:] for x in scores_by_category.columns]
    scores_by_category['Best Option'] = scores_by_category.T.idxmax()
    scores_by_category = scores_by_category
    st.subheader('Best option of each category:')
    st.write('Base Case is excluded')
    scores_by_category.iloc[:, -1:]
    
    #### Functionality to Export Results ####
    # Download data
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        for key in ('ProjectDescription', 'scores_by_category', 'OverallScore', 'OverallRank', 'UserInputs'):
            globals()[key].to_excel(writer, sheet_name=key)
        writer.save()

        st.download_button(
            label="Download data to Excel",
            data=buffer,
            file_name="nof-mca-tool.xlsx",
            mime="application/vnd.ms-excel"
        )

#### Sensitivities ####
# TODO
