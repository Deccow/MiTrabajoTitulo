package com.luceneapi.controller;

import java.util.List;
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.luceneapi.model.DictSearchResult;
import com.luceneapi.model.GlossSearchResult;
import com.luceneapi.service.LuceneService;

@RestController
@RequestMapping("/api")
public class LuceneController {

    private final LuceneService luceneService;

    public LuceneController(LuceneService luceneService) {
        this.luceneService = luceneService;
    }

    @GetMapping("/dict_search")
    public ResponseEntity<?> dict_search(
            @RequestParam String q,
            @RequestParam(defaultValue = "10") int max) {
        try {
            System.out.println("Searching for: " + q);

            List<DictSearchResult> results = luceneService.dict_search(q, max);
            return ResponseEntity.ok(Map.of(
                "query",   q,
                "count",   results.size(),
                "results", results
            ));
        } catch (Exception e) {
            System.err.println("Search error: " + e.getMessage());
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/gloss_search")
    public ResponseEntity<?> gloss_search(
            @RequestParam String q,
            @RequestParam(defaultValue = "10") int max) {
        try {
            List<GlossSearchResult> results = luceneService.gloss_search(q, max);
            return ResponseEntity.ok(Map.of(
                "query",   q,
                "count",   results.size(),
                "results", results
            ));
        } catch (Exception e) {
            System.err.println("Gloss search error: " + e.getMessage());
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }


    @GetMapping("/stats")
    public ResponseEntity<?> stats() {
        try {
            return ResponseEntity.ok(luceneService.stats());
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/dict_fields")
    public ResponseEntity<?> fields() {
        try {
            return ResponseEntity.ok(luceneService.getDictFields());
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/gloss_fields")
    public ResponseEntity<?> gloss_fields() {
        try {
            return ResponseEntity.ok(luceneService.getGlossFields());
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", e.getMessage()));
        }
    }
}
