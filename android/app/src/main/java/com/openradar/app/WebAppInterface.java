package com.openradar.app;

import android.webkit.JavascriptInterface;

public class WebAppInterface {
    private final DatabaseHelper dbHelper;

    public WebAppInterface(DatabaseHelper dbHelper) {
        this.dbHelper = dbHelper;
    }

    @JavascriptInterface
    public String getChapters() {
        return dbHelper.getChapters();
    }

    @JavascriptInterface
    public String getRubrics(int parentId, String q) {
        return dbHelper.getRubrics(parentId, q);
    }

    @JavascriptInterface
    public String searchRubrics(String q) {
        return dbHelper.searchRubrics(q);
    }

    @JavascriptInterface
    public String getRemedies(int rubricId) {
        return dbHelper.getRemedies(rubricId);
    }

    @JavascriptInterface
    public String getRemedyDetails(int id) {
        return dbHelper.getRemedyDetails(id);
    }
}
