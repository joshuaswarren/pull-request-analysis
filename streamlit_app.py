import requests
import pandas as pd
import streamlit as st
import os
import matplotlib.pyplot as pty

from datetime import datetime

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]


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

# Fetch pull requests
pull_requests = fetch_pull_requests()

# Create a DataFrame with the required fields
# Create a DataFrame with the required fields
data = []
label_count = {}
for pr in pull_requests:
    assignees = [assignee["login"] for assignee in pr["assignees"]]
    author = pr["user"]["login"]
    reviewers = [reviewer["login"] for reviewer in pr["requested_reviewers"]]
    created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    data.append({"id": pr["id"],
                 "title": pr["title"],
                 "author": author,
                 "assignees": assignees,
                 "reviewers": reviewers,
                 "created_at": created_at})
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
        if assignee in assignee_count:
            assignee_count[assignee] += 1
        else:
            assignee_count[assignee] = 1
    for reviewer in row.reviewers:
        if reviewer in reviewer_count:
            reviewer_count[reviewer] += 1
        else:
            reviewer_count[reviewer] = 1

# Display results with streamlit
st.title("Magento/magento2 Open Pull Requests")
if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(df)

# Visualization 1: Number of pull requests per month
df["created_month"] = df["created_at"].dt.to_period("M").astype(str)
monthly_counts = df["created_month"].value_counts().sort_index()
st.title("Open Pull Requests Per Month Opened")
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

fig, ax = pty.subplots(figsize=(10, 6))
selected_label_df.plot.pie(y="count", legend=False, autopct="%.1f%%", ax=ax)
ax.set_ylabel("")
st.pyplot(fig)
