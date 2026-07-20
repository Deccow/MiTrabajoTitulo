package com.luceneapi.model;

import java.util.List;

public class DictSearchResult {
    private List<String> lemmaWeight;
    private List<String> translationMapping;
    private List<String> verbatlasFrameId;
    private List<String> idSense;
    private List<String> lemma;
    private List<String> pronuAudio;
    private List<String> lemmaLanguage;
    private List<String> lemmaSensekey;
    private List<String> lemmaFrequence;
    private List<String> lemmaLanguageNormalizer;
    private List<String> pronuTransc;
    private List<String> synsetId;
    private List<String> pos;
    private List<String> category;
    private List<String> senseId;
    private List<String> version;
    private List<String> glossId;
    private List<String> languageLemma;
    private List<String> wordnetOffset;
    private List<String> type;
    private List<String> lemmaSource;
    private float score;

    public DictSearchResult(
            List<String> lemmaWeight, List<String> translationMapping, List<String> verbatlasFrameId,
            List<String> idSense, List<String> lemma, List<String> pronuAudio, List<String> lemmaLanguage,
            List<String> lemmaSensekey, List<String> lemmaFrequence, List<String> lemmaLanguageNormalizer,
            List<String> pronuTransc, List<String> synsetId, List<String> pos, List<String> category,
            List<String> senseId, List<String> version, List<String> id, List<String> languageLemma,
            List<String> wordnetOffset, List<String> type, List<String> lemmaSource, float score) {
        this.lemmaWeight            = lemmaWeight;
        this.translationMapping     = translationMapping;
        this.verbatlasFrameId       = verbatlasFrameId;
        this.idSense                = idSense;
        this.lemma                  = lemma;
        this.pronuAudio             = pronuAudio;
        this.lemmaLanguage          = lemmaLanguage;
        this.lemmaSensekey          = lemmaSensekey;
        this.lemmaFrequence         = lemmaFrequence;
        this.lemmaLanguageNormalizer = lemmaLanguageNormalizer;
        this.pronuTransc            = pronuTransc;
        this.synsetId               = synsetId;
        this.pos                    = pos;
        this.category               = category;
        this.senseId                = senseId;
        this.version                = version;
        this.glossId                = id;
        this.languageLemma          = languageLemma;
        this.wordnetOffset          = wordnetOffset;
        this.type                   = type;
        this.lemmaSource            = lemmaSource;
        this.score                  = score;
    }

    public List<String> getLemmaWeight()             { return lemmaWeight; }
    public List<String> getTranslationMapping()      { return translationMapping; }
    public List<String> getVerbatlasFrameId()        { return verbatlasFrameId; }
    public List<String> getIdSense()                 { return idSense; }
    public List<String> getLemma()                   { return lemma; }
    public List<String> getPronuAudio()              { return pronuAudio; }
    public List<String> getLemmaLanguage()           { return lemmaLanguage; }
    public List<String> getLemmaSensekey()           { return lemmaSensekey; }
    public List<String> getLemmaFrequence()          { return lemmaFrequence; }
    public List<String> getLemmaLanguageNormalizer() { return lemmaLanguageNormalizer; }
    public List<String> getPronuTransc()             { return pronuTransc; }
    public List<String> getSynsetId()                { return synsetId; }
    public List<String> getPos()                     { return pos; }
    public List<String> getCategory()                { return category; }
    public List<String> getSenseId()                 { return senseId; }
    public List<String> getVersion()                 { return version; }
    public List<String> getGlossId()                 { return glossId; }
    public List<String> getLanguageLemma()           { return languageLemma; }
    public List<String> getWordnetOffset()           { return wordnetOffset; }
    public List<String> getType()                    { return type; }
    public List<String> getLemmaSource()             { return lemmaSource; }
    public float  getScore()                   { return score; }
}
