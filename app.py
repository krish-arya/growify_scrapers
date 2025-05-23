import streamlit as st
import pandas as pd
import re
import time
import os
import requests
from apify_client import ApifyClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

# --- API KEYS ---
API_TOKEN = os.getenv("apify_api")
ACTOR_ID = os.getenv("actor_id")
WHATCMS_API = os.getenv("whatcms_api")

# Create Selenium Driver
def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    driver = webdriver.Chrome(options=options)
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver

# Engagement Rate Function
def get_engagement_rate(username):
    driver = create_driver()
    try:
        driver.get("https://www.clickanalytic.com/free-instagram-engagement-calculator/")

        input_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        input_box.clear()
        input_box.send_keys(username)

        submit_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Check Engagement Rate')]"))
        )
        submit_btn.click()

        WebDriverWait(driver, 20).until(lambda d: "%" in d.page_source)
        time.sleep(3)

        result_blocks = driver.find_elements(By.XPATH, "//div[contains(@class,'et_pb_text_inner')]")
        for block in result_blocks:
            if "%" in block.text:
                match = re.search(r"\d+\.?\d*%", block.text)
                if match:
                    rate = match.group(0)
                    driver.quit()
                    return rate

        driver.quit()
        return "Engagement rate not found."
    except Exception as e:
        driver.quit()
        return f"Error: {e}"

# Poll for actor run completion
def wait_for_actor_run(client, run_id, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        run = client.run(run_id).get()
        if run["status"] == "SUCCEEDED":
            return run["defaultDatasetId"]
        elif run["status"] in ["FAILED", "ABORTED", "TIMED-OUT"]:
            raise Exception(f"Actor run failed with status: {run['status']}")
        time.sleep(2)
    raise TimeoutError("Apify actor run did not finish in time.")

# Apify Instagram Info Function (FIXED HERE)
def fetch_instagram_info(usernames):
    client = ApifyClient(API_TOKEN)
    run = client.actor(ACTOR_ID).call(run_input={"usernames": usernames})
  # Positional input
    dataset_id = wait_for_actor_run(client, run["id"])
    info = {}
    for item in client.dataset(dataset_id).iterate_items():
        u = item.get("username")
        if u:
            info[u] = item
    return info


# DuckDuckGo Top 3 Links
def fetch_top_links(query):
    try:
        driver = create_driver()
        driver.get("https://html.duckduckgo.com/html/")

        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search_form_input_homepage"))
        )
        search_bar.clear()
        search_bar.send_keys(query)
        driver.find_element(By.ID, "search_button_homepage").click()

        # Wait for web-result blocks to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.web-result"))
        )
        result_blocks = driver.find_elements(By.CSS_SELECTOR, "div.web-result")

        top_links = []
        for block in result_blocks:
            anchor = block.find_element(By.CSS_SELECTOR, "a.result__url")
            href = anchor.get_attribute("href")
            if href and not any(domain in href for domain in ["instagram.com", "twitter.com", "x.com", "youtube.com", "youtu.be"]):
                top_links.append(href)
            if len(top_links) == 3:
                break

        driver.quit()
        return top_links
    except Exception as e:
        driver.quit()
        return [f"Error: {e}"]

# WhatCMS Detection
def detect_cms(url):
    try:
        response = requests.get(
            "https://whatcms.org/APIEndpoint/Detect",
            params={"key": WHATCMS_API, "url": url},
            timeout=10
        )
        data = response.json()
        if data.get("result", {}).get("code") == 200:
            cms = data["result"].get("name", "Unknown")
            confidence = data["result"].get("confidence", "N/A")
            return cms, confidence
        else:
            return "Unknown", "N/A"
    except Exception as e:
        return f"Error: {e}", "N/A"

# -------------------- Streamlit UI --------------------

st.set_page_config(page_title="Instagram & Designer Info", layout="centered")
st.title("🎯 Instagram & Designer Intelligence Tool")

# Initialize session state
for key in ["insta_usernames", "username", "designer_names", "insta_info", "engagement_rate"]:
    if key not in st.session_state:
        st.session_state[key] = ""

if "search_results" not in st.session_state:
    st.session_state.search_results = {}

if "cms_results" not in st.session_state:
    st.session_state.cms_results = {}

if "selected_links" not in st.session_state:
    st.session_state.selected_links = {}

# Instagram Info Section
st.header("📸 Instagram Handle Lookup")
st.session_state["insta_usernames"] = st.text_area(
    "Enter Instagram Handles (comma separated)",
    value=st.session_state["insta_usernames"]
)

if st.button("Fetch Instagram Info"):
    usernames = [u.strip().lstrip("@") for u in st.session_state["insta_usernames"].split(",") if u.strip()]
    if usernames:
        info = fetch_instagram_info(usernames)
        df = pd.DataFrame([{
            "Username": u,
            "Full Name": info[u].get("fullName"),
            "Followers": info[u].get("followersCount"),
            "Following": info[u].get("followsCount"),
            "Verified": info[u].get("verified"),
            "Business": info[u].get("isBusinessAccount"),
            "Joined Recently": info[u].get("joinedRecently"),
            "URL": info[u].get("url"),
            "Bio": info[u].get("biography")
        } for u in usernames if u in info])
        st.session_state["insta_info"] = df

if isinstance(st.session_state["insta_info"], pd.DataFrame):
    st.dataframe(st.session_state["insta_info"])

# Engagement Rate Section
st.header("📊 Engagement Rate Calculator")
st.session_state["username"] = st.text_input(
    "Enter Instagram Handle (single)",
    value=st.session_state["username"]
)

if st.button("Calculate Engagement Rate"):
    clean_user = st.session_state["username"].strip().lstrip("@")
    if clean_user:
        st.session_state["engagement_rate"] = get_engagement_rate(clean_user)

if st.session_state["engagement_rate"]:
    st.success(f"Engagement Rate: {st.session_state['engagement_rate']}")

# Designer Search + CMS Detection
st.header("🎨 Designer Search Links + CMS Detection")
st.session_state["designer_names"] = st.text_area(
    "Enter Designer Names (one per line)",
    value=st.session_state["designer_names"]
)

if st.button("Search Designers"):
    names = [n.strip() for n in st.session_state["designer_names"].split("\n") if n.strip()]
    for name in names:
        links = fetch_top_links(f"{name} designer official website")
        st.session_state.search_results[name] = links

# Show search results and CMS detection
if "search_results" in st.session_state:
    for name, links in st.session_state.search_results.items():
        if links:
            st.subheader(f"{name}")
            selected_link = st.radio(
                f"Top links for {name}", links,
                key=f"radio_{name}",
                index=0
            )
            st.session_state.selected_links[name] = selected_link

            if (name, selected_link) not in st.session_state.cms_results:
                cms, confidence = detect_cms(selected_link)
                st.session_state.cms_results[(name, selected_link)] = (cms, confidence)

            cms, confidence = st.session_state.cms_results.get((name, selected_link), ("Unknown", "N/A"))
            st.write(f"*Selected Link:* [{selected_link}]({selected_link})")
            st.write(f"*CMS:* {cms} | *Confidence:* {confidence}")
        else:
            st.warning(f"No valid links found for {name}.")