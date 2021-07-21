import streamlit as st
import base64
from spacy import displacy
import spacy
from textblob import TextBlob
import streamlit.components.v1 as components
import codecs
from heapq import nlargest
from gtts import gTTS
from googletrans import Translator
from spacy.lang.en.stop_words import STOP_WORDS
import emoji
from string import punctuation
import warnings
warnings.filterwarnings('ignore')
import glob
import os
import re
import time 
timestr = time.strftime("%Y%m%d-%H%M%S")

#################

st.set_page_config(page_title='PTOP', page_icon=":book:")

padding = 0
st.markdown(f""" <style>
    .reportview-container .main .block-container{{
        padding-top: {padding}rem;
        padding-right: {padding}rem;
        padding-left: {padding}rem;
        padding-bottom: {padding}rem;
    }} </style> """, unsafe_allow_html=True)


st.markdown(""" <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style> """, unsafe_allow_html=True)

#################
try:
    os.mkdir("temp")
except:
    pass

nlp = spacy.load('en_core_web_sm')
HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; color:white; background-color:#FD2D00;">{}</div>"""

#summary funtion 
def summary(text):
    
    k=[]
    a=[]
    summa=[]
    k=text.split("\n")
    for i in k:
        if i!='':
            a.append(i)
    
    
    stopwords = list(STOP_WORDS)

    #spacy.cli.download("en")
    nlp = spacy.load('en_core_web_sm')
    
    
    for x in a:
        doc = nlp(x)

        tokens = [token.text for token in doc]
        
        word_frequencies = {}
        for word in doc:
            if word.text.lower() not in stopwords:
                if word.text.lower() not in punctuation:
                    if word.text not in word_frequencies.keys():
                        word_frequencies[word.text] = 1
                    else:
                        word_frequencies[word.text] += 1

        
        try:
            max_frequency = max(word_frequencies.values())
        except:
            return ""
        
        for word in word_frequencies.keys():
            word_frequencies[word] = word_frequencies[word]/max_frequency

      
        sentence_tokens = [sent for sent in doc.sents]
  
        sentence_scores = {}
        for sent in sentence_tokens:
            for word in sent:
                if word.text.lower() in word_frequencies.keys():
                    if sent not in sentence_scores.keys():
                        sentence_scores[sent] = word_frequencies[word.text.lower()]
                    else:
                        sentence_scores[sent] += word_frequencies[word.text.lower()]


        #Now obtain 30% of sentence with maximum score and is done by heapq
        select_length = int(len(sentence_tokens)*0.3)
        if (select_length<1):
            select_length = 1
      
        summary = nlargest(select_length, sentence_scores, key=sentence_scores.get)
       
        final_summary = [word.text for word in summary]
        summary = ' '.join(final_summary)
        summa.append(summary)
        
    complete = " ".join(summa)
    return complete

# Reading Time
def readingTime(docs):
    total_words_tokens =  [ token.text for token in nlp(docs)]
    estimatedtime  = len(total_words_tokens)/200
    return 'The estimated reading time for your text is {} min(s).'.format(round(estimatedtime))

@st.cache(show_spinner=False)
def text_to_speech1(summ):
    tts = gTTS(summ)
    try:
        my_file_name = summ[0:20]
    except:
        my_file_name = "audio"
    tts.save(f"temp/{my_file_name}.mp3")
    return my_file_name

# Functions to Sanitize and Redact 
def sanitize_names(text):
    docx = nlp(text)
    censored_sentences = []
    
    for token in docx:
        if token.ent_type_ == 'PERSON':
            censored_sentences.append("[CENSORED TEXT] ")
        else:
            censored_sentences.append(token.text_with_ws)
    return "".join(censored_sentences)
def sanitize_places(text):
    docx = nlp(text)
    censored_sentences = []
    
    for token in docx:
        if token.ent_type_ == 'GPE':
            censored_sentences.append("[CENSORED TEXT] ")
        else:
            censored_sentences.append(token.text_with_ws)
    return "".join(censored_sentences)
def sanitize_date(text):
    docx = nlp(text)
    censored_sentences = []
    
    for token in docx:
        if token.ent_type_ == 'DATE':
            censored_sentences.append("[CENSORED TEXT] ")
        else:
            censored_sentences.append(token.text_with_ws)
    return "".join(censored_sentences)
def sanitize_org(text):
    docx = nlp(text)
    censored_sentences = []
    
    for token in docx:
        if token.ent_type_ == 'ORG':
            censored_sentences.append("[CENSORED TEXT] ")
        else:
            censored_sentences.append(token.text_with_ws)
    return "".join(censored_sentences)


#@st.cache
def render_entities(rawtext):
    docx = nlp(rawtext)
    html = displacy.render(docx,style="ent")
    html = html.replace("\n\n","\n")
    result = HTML_WRAPPER.format(html)
    return result

def text_downloader(raw_text):
    b64 = base64.b64encode(raw_text.encode()).decode()
    newfilename= "censored_text_{}_.txt".format(timestr)
    st.markdown(":point_down: Download text file ")
    href = f'<a href="data:file/txt;base64,{b64}" download = "{newfilename}">Click Here !!</a>'
    st.markdown(href, unsafe_allow_html=True)

# Custom Components Fxn
def st_calculator(calc_html,width=1000,height=1350):
    calc_file = codecs.open(calc_html,'r')
    page = calc_file.read()
    components.html(page,width=width,height=height,scrolling=False)

@st.cache(show_spinner=False)   
def text_to_speech(input_language, output_language, text, tld):
    translator = Translator()
    translation = translator.translate(text, src=input_language, dest=output_language)
    trans_text = translation.text
    tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
    try:
        my_file_name = text[0:20]+tld[:]
    except:
        my_file_name = "audio"
    tts.save(f"temp/{my_file_name}.mp3")
    return my_file_name, trans_text

def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    if len(mp3_files) != 0:
        now = time.time()
        n_days = n * 86400
        for f in mp3_files:
            if os.stat(f).st_mtime < now - n_days:
                os.remove(f)
                print("Deleted ", f)





def main():
    Features = ["Summary","Censor", "Sentimoji","Translator"]
    choice = st.sidebar.selectbox("Select Tool", Features)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Hey There :wave:")
    st.sidebar.markdown("""This app, PTOP (Process Text at One Place), made by <a href="https://www.linkedin.com/in/tarun-kumar-singh-984b441b5/">Tarun</a>.""", unsafe_allow_html=True)
    st.sidebar.markdown("""Check out my <a href="https://github.com/tarun4ml">github</a> for source code.""", unsafe_allow_html=True)
    if choice == "Summary":
        html_temp = """
    <div style="background-color:#FD2D00;border-radius: 5px;"><p style="color:white;font-size:60px;text-align:center;">Text Summarizer</p></div>
    """
        components.html(html_temp)
        text = st.text_area("Enter Text For Summary",height=300)
        try:
            if st.button("Estimate time"):
                st.success(readingTime(text))
            if st.button("summarize"):
                summ = summary(text)
                st.success(summ)
                with st.spinner(text="Generating audio of summary"):

                    result = text_to_speech1(summ)
                    audio_file = open(f"temp/{result}.mp3", "rb")
                    audio_bytes = audio_file.read()
                    st.subheader("Audio:")
                    st.audio(audio_bytes, format='audio/mp3')
        except:
            st.error(':negative_squared_cross_mark: An error occured :negative_squared_cross_mark: Sorry for inconvenience :disappointed:')
        
    
    if choice == "Censor":
        html_temp = """
    <div style="background-color:#FD2D00;border-radius: 5px;"><p style="color:white;font-size:60px;text-align:center;">Text Censor</p></div>
    """
        
        components.html(html_temp)
        rawtext = st.text_area("Enter Text to Censor",height=300)
        redaction_choice = st.multiselect("Select Item(s) to Censor", ("names","places","org","date"))
        st.subheader("Do you have some custom words to be censored?")
        st.markdown(
            "Write the words you are looking for, separated by a comma.")
        st.markdown("*Eg: word1, word2, word3*")
        w = st.text_input("")
        result = rawtext
        try:
            if st.button("Submit"):
                with st.spinner(text="Generating audio of summary"):

                    for i in range(len(redaction_choice)) :
                        if redaction_choice[i] == 'names':
                            result = sanitize_names(result)
                        elif redaction_choice[i] == 'places':
                            result = sanitize_places(result)
                        elif redaction_choice[i] == 'date':
                            result = sanitize_date(result)
                        elif redaction_choice[i] == 'org':
                            result = sanitize_org(result)
                        else:
                            result = sanitize_names(result)
                    components.html(render_entities(rawtext), height=300, scrolling = True)
                    if w != "":
                            w = w.split(", ")
                            w = [lw.lower() for lw in w]
                            for eachword in re.split('[, . ; - :]', result):
                                if eachword.lower() in w:
                                    result = result.replace(eachword, "[CENSORED TEXT]")
                    st.success(str(f"{result}"))
                    text_downloader(result)
        except:
            st.error(':negative_squared_cross_mark: An error occured :negative_squared_cross_mark: Sorry for inconvenience :disappointed:')
            
    if choice == 'Sentimoji':
        html_temp = """
    <div style="background-color:#FD2D00;border-radius: 5px;"><p style="color:white;font-size:60px;text-align:center;">Sentiment Analyzer</p></div>
    """
        html_emoji = """<div style="font-size:5rem;width:100%;text-align:center;">{}</div>"""
        
        components.html(html_temp)
        rawtext = st.text_area("Enter Text to Analyze",height=300)
        try:
            if st.button("Analyze"):
                with st.spinner(text="Please wait, analyzing"):
                    blob = TextBlob(rawtext)
                    result = blob.sentiment.polarity
                    if result > 0.0:
                        custom_emoji = ':smile:'
                        emo = emoji.emojize(custom_emoji,use_aliases=True)
                        components.html(html_emoji.format(emo))
                    elif result < 0.0:
                        custom_emoji = ':disappointed:'
                        emo = emoji.emojize(custom_emoji,use_aliases=True)
                        components.html(html_emoji.format(emo))
                    else:
                        custom_emoji = ':neutral_face:'
                        emo = emoji.emojize(custom_emoji,use_aliases=True)
                        components.html(html_emoji.format(emo))
                    st.info("Polarity Score is {}".format(result))
                    st.write("Polarity lies between [-1,1], -1 defines a negative sentiment and 1 defines a positive sentiment.") 
        except:
            st.error(':negative_squared_cross_mark: An error occured :negative_squared_cross_mark: Sorry for inconvenience :disappointed:')

    if choice == "Translator":
        html_temp = """
    <div style="background-color:#FD2D00;border-radius: 5px;"><p style="color:white;font-size:60px;text-align:center;">Translator</p></div>
    """
        components.html(html_temp)
        

        text = st.text_area("Enter text for Translation",height=75)
        in_lang = st.selectbox(
            "Select your input language",
            ("English", "Hindi", "Bengali", "korean", "Chinese", "Japanese"),
        )
        if in_lang == "English":
            input_language = "en"
        elif in_lang == "Hindi":
            input_language = "hi"
        elif in_lang == "Bengali":
            input_language = "bn"
        elif in_lang == "korean":
            input_language = "ko"
        elif in_lang == "Chinese":
            input_language = "zh-cn"
        elif in_lang == "Japanese":
            input_language = "ja"

        out_lang = st.selectbox(
            "Select your output language",
            ("English", "Hindi", "Bengali", "korean", "Chinese", "Japanese"),
        )
        if out_lang == "English":
            output_language = "en"
        elif out_lang == "Hindi":
            output_language = "hi"
        elif out_lang == "Bengali":
            output_language = "bn"
        elif out_lang == "korean":
            output_language = "ko"
        elif out_lang == "Chinese":
            output_language = "zh-CN"
        elif out_lang == "Japanese":
            output_language = "ja"
        
        tld = "com"
        if out_lang == "English":
            with st.spinner(text="Please Wait"):
                english_accent = st.selectbox(
                    "Select your english accent",
                    (
                        "Default",
                        "India",
                        "United Kingdom",
                        "United States",
                        "Canada",
                        "Australia",
                        "Ireland",
                        "South Africa",
                    ),
                )

                if english_accent == "Default":
                    tld = "com"
                elif english_accent == "India":
                    tld = "co.in"

                elif english_accent == "United Kingdom":
                    tld = "co.uk"
                elif english_accent == "United States":
                    tld = "com"
                elif english_accent == "Canada":
                    tld = "ca"
                elif english_accent == "Australia":
                    tld = "com.au"
                elif english_accent == "Ireland":
                    tld = "ie"
                elif english_accent == "South Africa":
                    tld = "co.za"
        display_output_text = st.checkbox("Display translated text")

        try:
            if st.button("Translate"):
                with st.spinner(text="Translating"):
                    result, output_text = text_to_speech(input_language, output_language, text, tld)
                    audio_file = open(f"temp/{result}.mp3", "rb")
                    audio_bytes = audio_file.read()
                    st.subheader("Your audio:")
                    st.audio(audio_bytes, format="audio/mp3", start_time=0)

                    if display_output_text:
                        st.subheader("Translated text:")
                        st.write(f" {output_text}")
        except:
            st.error(':negative_squared_cross_mark: An error occured :negative_squared_cross_mark: Sorry for inconvenience :disappointed:')
    remove_files(1)
        
if __name__ == '__main__':
    main()

