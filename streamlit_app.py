import streamlit as st
import pandas as pd
import numpy as np
import os
from decouple import config

GITHUB_TOKEN=config('GITHUB_TOKEN')

st.title('Magento Pull Requests')

@st.cache_data
def load_data():
## using the GitHub web API download all available data about every open pull request on the magento/magento2 repo
    url = 'https://api.github.com/repos/magento/magento2/pulls?state=open&per_page=100&page={page}'
    page = 1
    data = []
    while True:
        response = requests.get(url.format(page=page), headers={'Authorization': 'token ' + GITHUB_TOKEN})
        if not response.ok:
            break
        data.extend(response.json())
        page += 1
    return pd.DataFrame(data)

data_load_state = st.text('Loading data...')
data = load_data()
data_load_state.text('Loading data...done!')
