import streamlit as st
import pandas as pd
import numpy as np

st.title('Magento Pull Requests')

@st.cache_data
def load_data():
