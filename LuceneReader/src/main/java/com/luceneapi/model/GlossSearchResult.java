package com.luceneapi.model;

import java.util.List;

public class GlossSearchResult {

    private List<String> gloss;
    private List<String> version;
    private List<String> example;
    private List<String> id;
    private float score;

    public GlossSearchResult(List<String> gloss, List<String> version, List<String> example, List<String> id, float score) {
        this.gloss = gloss;
        this.version = version;
        this.example = example;
        this.id = id;
        this.score = score;
    }

    public List<String> getGloss() { return gloss; }
    public List<String> getVersion() { return version; }
    public List<String> getExample() { return example; }
    public List<String> getId() { return id; }

}
