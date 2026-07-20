package com.luceneapi.service;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.core.KeywordAnalyzer;
import org.apache.lucene.analysis.miscellaneous.PerFieldAnalyzerWrapper;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.LeafReaderContext;
import org.apache.lucene.index.Term;
import org.apache.lucene.queryparser.classic.MultiFieldQueryParser;
import org.apache.lucene.search.Explanation;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TermQuery;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.luceneapi.model.DictSearchResult;
import com.luceneapi.model.GlossSearchResult;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;



@Service
public class LuceneService {

    @Value("${lucene.index.dict_path:./lucene-index}")
    private String dict_path;

    @Value("${lucene.index.gloss_path:./lucene-index}")
    private String gloss_path;

    @Value("${lucene.index.lexicon_path:./lucene-index}")
    private String lexicon_path;

    private StandardAnalyzer analyzer;
    private Directory dict_directory;
    private Directory gloss_directory;
    private Directory lexicon_directory;

    @PostConstruct
    public void init() throws IOException {
        analyzer  = new StandardAnalyzer();
        dict_directory = FSDirectory.open(Path.of(dict_path));
        System.out.println("LuceneService initialized with dict_path: " + dict_path);
        gloss_directory = FSDirectory.open(Path.of(gloss_path));
        System.out.println("LuceneService initialized with gloss_path: " + gloss_path);
        lexicon_directory = FSDirectory.open(Path.of(lexicon_path));
    }

    
    private static List<String> getAll(Document doc, String field) {
        return Arrays.asList(doc.getValues(field));
    }


    //  Dict Search

    public List<DictSearchResult> dict_search(String queryStr, int maxResults) throws Exception {
        List<DictSearchResult> results = new ArrayList<>();

        if (!DirectoryReader.indexExists(dict_directory)) {
            return results;
        }

        try (DirectoryReader reader = DirectoryReader.open(dict_directory)) {
            IndexSearcher searcher = new IndexSearcher(reader);

            Map<String, Analyzer> fieldAnalyzers = new HashMap<>();
            fieldAnalyzers.put("LANGUAGE_LEMMA",  new KeywordAnalyzer());
            fieldAnalyzers.put("LEMMA_LANGUAGE",  new KeywordAnalyzer());
            fieldAnalyzers.put("SYNSET_ID",       new KeywordAnalyzer());
            fieldAnalyzers.put("POS",             new KeywordAnalyzer());
            fieldAnalyzers.put("CATEGORY",        new KeywordAnalyzer());
            fieldAnalyzers.put("ID",              new KeywordAnalyzer());
            fieldAnalyzers.put("TYPE",            new KeywordAnalyzer());
            fieldAnalyzers.put("LEMMA",            new KeywordAnalyzer());
            fieldAnalyzers.put("SENSE_ID",     new KeywordAnalyzer());

            PerFieldAnalyzerWrapper perFieldAnalyzer = new PerFieldAnalyzerWrapper(analyzer, fieldAnalyzers);

            

            MultiFieldQueryParser parser = new MultiFieldQueryParser(
                new String[]{"LEMMA", "LEMMA_LANGUAGE", "LANGUAGE_LEMMA", "SYNSET_ID", "POS", "CATEGORY", "TYPE", "SENSE_ID"},
                perFieldAnalyzer
            );
            parser.setAllowLeadingWildcard(true);

            //String escapedQueryStr = MultiFieldQueryParser.escape(queryStr);
            Query query = parser.parse(queryStr);
            System.out.println("Parsed query: " + query.toString());

            Query q = new TermQuery(new Term("TYPE", "CONCEPT"));
            TopDocs hitsNE  = searcher.search(q, maxResults);
            System.out.println("NAMED_ENTITY hits: " + hitsNE.totalHits.value);

            TopDocs hits  = searcher.search(query, maxResults);

            for (ScoreDoc sd : hits.scoreDocs) {
                Document doc = searcher.doc(sd.doc);
                Explanation explain = searcher.explain(query, sd.doc);
                System.out.println(explain);
                results.add(new DictSearchResult(
                    getAll(doc, "LEMMA_WEIGHT"),
                    getAll(doc, "TRANSLATION_MAPPING"),
                    getAll(doc, "VERBATLAS_FRAME_ID"),
                    getAll(doc, "ID_SENSE"),
                    getAll(doc, "LEMMA"),
                    getAll(doc, "PRONU_AUDIO"),
                    getAll(doc, "LEMMA_LANGUAGE"),
                    getAll(doc, "LEMMA_SENSEKEY"),
                    getAll(doc, "LEMMA_FREQUENCE"),
                    getAll(doc, "LANGUAGE_LEMMA_NORMALIZER"),
                    getAll(doc, "PRONU_TRANSC"),
                    getAll(doc, "SYNSET_ID"),
                    getAll(doc, "POS"),
                    getAll(doc, "CATEGORY"),
                    getAll(doc, "SENSE_ID"),
                    getAll(doc, "VERSION"),
                    getAll(doc, "ID"),
                    getAll(doc, "LANGUAGE_LEMMA"),
                    getAll(doc, "WORDNET_OFFSET"),
                    getAll(doc, "TYPE"),
                    getAll(doc, "LEMMA_SOURCE"),
                    sd.score
                ));
            }
        }
        return results;
    }

    //  Gloss Search

    public List<GlossSearchResult> gloss_search(String queryStr, int maxResults) throws Exception {
        List<GlossSearchResult> results = new ArrayList<>();
        
        if (!DirectoryReader.indexExists(gloss_directory)) {
            return results;
        }

        try (DirectoryReader reader = DirectoryReader.open(gloss_directory)) {
            IndexSearcher searcher = new IndexSearcher(reader);
            
            Query query = new TermQuery(new Term("ID", queryStr)
);
            TopDocs hits  = searcher.search(query, maxResults);

            for (ScoreDoc sd : hits.scoreDocs) {
                Document doc = searcher.doc(sd.doc);
                results.add(new GlossSearchResult(
                    getAll(doc, "GLOSS"),
                    getAll(doc, "VERSION"),
                    getAll(doc, "EXAMPLE"),
                    getAll(doc, "ID"),
                    sd.score
                ));
            }
        }


        return results;
    }



    public Map<String, Object> stats() throws IOException {
        if (!DirectoryReader.indexExists(dict_directory)) {
            return Map.of("documents", 0, "dict_path", dict_path);
        }
        try (DirectoryReader reader = DirectoryReader.open(dict_directory)) {
            return Map.of(
                "documents", reader.numDocs(),
                "dict_path", dict_path
            );
        }
    }

    public Map<String, Object> getDictFields() throws IOException {
        try (DirectoryReader reader = DirectoryReader.open(dict_directory)) 
        {
            Set<String> fields = new HashSet<>();
            for (LeafReaderContext ctx : reader.leaves()) 
            {
                ctx.reader().getFieldInfos().forEach(f -> fields.add(f.name));
            }
            return Map.of("fields", fields);
        }
    }

    public Map<String, Object> getGlossFields() throws IOException {
        try (DirectoryReader reader = DirectoryReader.open(gloss_directory)) 
        {
            Set<String> fields = new HashSet<>();
            for (LeafReaderContext ctx : reader.leaves()) 
            {
                ctx.reader().getFieldInfos().forEach(f -> fields.add(f.name));
            }
            return Map.of("fields", fields);
        }
    }

    @PreDestroy
    public void close() throws IOException {
        if (dict_directory != null) dict_directory.close();
        if (gloss_directory != null) gloss_directory.close();
        if (lexicon_directory != null) lexicon_directory.close();
        if (analyzer  != null) analyzer.close();
    }


}