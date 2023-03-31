import requests
import pandas as pd
import streamlit as st
import os
import matplotlib.pyplot as pty
from datetime import datetime

st.set_page_config(page_title="Open Magento 2 Pull Requests", page_icon=":octocat:", layout="wide")

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

@st.cache_data
def fetch_adobe_membership(user_url):
    headers = {'Authorization': 'Bearer ' + GITHUB_TOKEN}
    response = requests.get(user_url + '/orgs', headers=headers)
    if response.status_code == 200:
        orgs = response.json()
        for org in orgs:
            if org["login"] == "Adobe":
                return True
    return False

def add_adobe_suffix(users):
    for user in users:
        if fetch_adobe_membership(user["url"]):
            user["login"] += " (Adobe)"
    return users

@st.cache_data
def fetch_pull_requests():
    headers= {'Authorization': 'Bearer ' + GITHUB_TOKEN}
    pull_requests = []
    page = 1
    url = 'https://api.github.com/repos/magento/magento2/pulls?state=open&per_page=100&page={page}'
    while True:
        response = requests.get(url.format(page=page), headers=headers)
        if response.status_code == 200:
            data = response.json()
            if not data:
                break
            pull_requests.extend(data)
            page += 1
        else:
            st.error("Error fetching pull requests")
            st.write(response.json())
            raise SystemExit
    return pull_requests

def display_paginated_table(df):
    # Filter labels that start with "Progress:"
    def filter_progress_labels(labels):
        return [label for label in labels if label.startswith("Progress:")]

    # Convert list of names to a formatted string
    def format_names_list(names):
        if not names:
            return ""
        if isinstance(names[0], dict):
            names = [name["login"] for name in names]
        return ", ".join(names)

    # Display paginated table
    st.title("Oldest Open Pull Requests By Time Since Last Update")
    page_size = 10
    num_pages = int(-(-len(df) // page_size))
    page = st.number_input("Select a page:", min_value=1, max_value=num_pages, value=1)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    # Display table in a columnar format
    rows_to_display = df.iloc[start_idx:end_idx].copy()

    # Apply the filter_progress_labels and format_names_list functions
    rows_to_display["Labels"] = rows_to_display["labels"].apply(filter_progress_labels)
    rows_to_display["Assignees"] = rows_to_display["assignees"].apply(format_names_list)
    rows_to_display["Reviewers"] = rows_to_display["reviewers"].apply(format_names_list)

    rows_to_display["created_at"] = rows_to_display["created_at"].dt.strftime("%Y-%m-%d")
    rows_to_display["updated_at"] = rows_to_display["updated_at"].dt.strftime("%Y-%m-%d")

    # Format the Link column
    rows_to_display["Link"] = rows_to_display["html_url"].apply(
        lambda url: f'<a href="{url}" target="_blank">{url.split("/")[-1]}</a>'
    )


    # rows_to_display["labels"] = rows_to_display["labels"].apply(get_progress_label)

    # Display the table with proper HTML rendering
    st.write(
        rows_to_display[["title", "Link", "Labels", "created_at", "updated_at", "author", "Assignees", "Reviewers"]]
        .rename(
            columns={
                "title": "Title",
                "author": "Author",
            }
        )
        .style.hide_index()
        .set_table_attributes('class="table"')
        .set_properties(**{'white-space': 'nowrap'})
        .render("html", escape=False),
        unsafe_allow_html=True,
    )



# Fetch pull requests
pull_requests = fetch_pull_requests()

# Create a DataFrame with the required fields
# Create a DataFrame with the required fields
data = []
label_count = {}
for pr in pull_requests:
    assignees = [{"login": assignee["login"], "url": assignee["url"]} for assignee in pr["assignees"]]
    author = pr["user"]["login"]
    reviewers = [{"login": reviewer["login"], "url": reviewer["url"]} for reviewer in pr["requested_reviewers"]]
    created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    updated_at = datetime.strptime(pr["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
    data.append({"id": pr["id"],
                 "title": pr["title"],
                 "author": author,
                 "assignees": add_adobe_suffix(assignees),
                 "reviewers": add_adobe_suffix(reviewers),
                 "created_at": created_at,
                 "updated_at": updated_at,
                 "html_url": pr["html_url"],
                 "labels": [label["name"] for label in pr["labels"]]})
    for label in pr["labels"]:
        label_name = label["name"]
        if label_name in label_count:
            label_count[label_name] += 1
        else:
            label_count[label_name] = 1
df = pd.DataFrame(data)

# Count assignees and reviewers
assignee_count = {}
reviewer_count = {}
for row in df.itertuples():
    for assignee in row.assignees:
        assignee_login = assignee["login"]
        if assignee_login in assignee_count:
            assignee_count[assignee_login] += 1
        else:
            assignee_count[assignee_login] = 1
    for reviewer in row.reviewers:
        reviewer_login = reviewer["login"]
        if reviewer_login in reviewer_count:
            reviewer_count[reviewer_login] += 1
        else:
            reviewer_count[reviewer_login] = 1

# Display results with streamlit
st.title("Magento Open Pull Requests")
st.write("Based on data from the GitHub API for https://github.com/magento/magento2")
st.write("Powered by https://github.com/joshuaswarren/pull-request-analysis")
if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(df)


# Visualization 0: Open Pull Requests That Have Gone Longest Without an Update
df = df.sort_values("updated_at", ascending=True)
display_paginated_table(df)

# Visualization 1: Number of pull requests per month
df["created_month"] = df["created_at"].dt.to_period("M").astype(str)
monthly_counts = df["created_month"].value_counts().sort_index()
st.title("Open Pull Requests Per Month Created")
st.bar_chart(monthly_counts)

# Visualization 2: Assignee count
assignee_df = pd.DataFrame.from_dict(assignee_count, orient="index", columns=["count"]).sort_values(by="count", ascending=False)
st.title("Assignees with Open Pull Requests")
st.write(assignee_df)

# Visualization 3: Reviewer count
reviewer_df = pd.DataFrame.from_dict(reviewer_count, orient="index", columns=["count"]).sort_values(by="count", ascending=False)
st.title("Reviewers with Open Pull Requests")
st.write(reviewer_df)

# Visualization 4: Label count
label_df = pd.DataFrame.from_dict(label_count, orient="index", columns=["count"]).sort_values(by="count", ascending=False)
st.title("Number of Open Pull Requests per Label")
st.write(label_df)

# Visualization 5: Number of pull requests per year
df["created_year"] = df["created_at"].dt.to_period("Y").astype(str)
yearly_counts = df["created_year"].value_counts().sort_index()
st.title("Open Pull Requests Per Year Opened")
st.bar_chart(yearly_counts)

# Visualization 6: Pie chart for selected labels
selected_labels = ["Progress: pending review", "Progress: ready for testing", "Progress: review", "Progress: needs update",
                   "Progress: extended testing", "Progress: accept", "Progress: pending approval", "progress: to approve",
                   "Progress: on hold"]
selected_label_counts = {label: label_count.get(label, 0) for label in selected_labels}
selected_label_df = pd.DataFrame.from_dict(selected_label_counts, orient="index", columns=["count"])
st.title("Open Pull Requests by Progress Labels")
st.write(selected_label_df)

fig, ax = pty.subplots(figsize=(5, 3))
selected_label_df.plot.pie(y="count", legend=False, autopct="%.1f%%", ax=ax)
ax.set_ylabel("")
st.pyplot(fig)

