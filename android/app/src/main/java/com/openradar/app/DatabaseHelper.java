package com.openradar.app;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.List;

public class DatabaseHelper {
    private static final String TAG = "OpenRadarDB";
    private static final String DB_NAME = "openradar.db";
    private final Context context;
    private SQLiteDatabase database;

    public DatabaseHelper(Context context) {
        this.context = context;
        initializeDatabase();
    }

    private void initializeDatabase() {
        File dbDir = new File(context.getApplicationInfo().dataDir + "/databases");
        if (!dbDir.exists()) {
            dbDir.mkdirs();
        }

        File dbFile = new File(dbDir, DB_NAME);
        if (!dbFile.exists() || dbFile.length() == 0) {
            try {
                Log.i(TAG, "Extracting openradar.db from assets to " + dbFile.getAbsolutePath());
                InputStream is = context.getAssets().open(DB_NAME);
                OutputStream os = new FileOutputStream(dbFile);
                byte[] buffer = new byte[64 * 1024];
                int length;
                while ((length = is.read(buffer)) > 0) {
                    os.write(buffer, 0, length);
                }
                os.flush();
                os.close();
                is.close();
                Log.i(TAG, "Database extraction completed successfully.");
            } catch (Exception e) {
                Log.e(TAG, "Failed to copy database from assets", e);
            }
        }

        try {
            database = SQLiteDatabase.openDatabase(dbFile.getAbsolutePath(), null, SQLiteDatabase.OPEN_READONLY);
            Log.i(TAG, "SQLite database opened successfully.");
        } catch (Exception e) {
            Log.e(TAG, "Failed to open SQLite database", e);
        }
    }

    public String getChapters() {
        JSONArray arr = new JSONArray();
        if (database == null) return "[]";
        try (Cursor cursor = database.rawQuery("SELECT id, order_idx as ord, name FROM chapters ORDER BY order_idx;", null)) {
            while (cursor.moveToNext()) {
                JSONObject obj = new JSONObject();
                obj.put("id", cursor.getInt(0));
                obj.put("ord", cursor.getInt(1));
                obj.put("name", cursor.getString(2));
                arr.put(obj);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error in getChapters", e);
        }
        return arr.toString();
    }

    public String getRubrics(int parentId, String q) {
        JSONArray arr = new JSONArray();
        if (database == null) return "[]";
        String sql;
        String[] args;
        if (q != null && !q.trim().isEmpty()) {
            sql = "SELECT id, parent_id, level, has_child, text, parent_path, full_path, remedy_count " +
                  "FROM rubrics WHERE parent_id = ? AND text LIKE ? ORDER BY order_idx, suborder_idx LIMIT 100;";
            args = new String[]{String.valueOf(parentId), "%" + q.trim() + "%"};
        } else {
            sql = "SELECT id, parent_id, level, has_child, text, parent_path, full_path, remedy_count " +
                  "FROM rubrics WHERE parent_id = ? ORDER BY order_idx, suborder_idx LIMIT 100;";
            args = new String[]{String.valueOf(parentId)};
        }

        try (Cursor cursor = database.rawQuery(sql, args)) {
            while (cursor.moveToNext()) {
                JSONObject obj = new JSONObject();
                obj.put("id", cursor.getInt(0));
                obj.put("parent_id", cursor.getInt(1));
                obj.put("level", cursor.getInt(2));
                obj.put("has_child", cursor.getInt(3));
                obj.put("text", cursor.getString(4));
                obj.put("parent_path", cursor.getString(5));
                obj.put("full_path", cursor.getString(6));
                obj.put("remedy_count", cursor.getInt(7));
                arr.put(obj);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error in getRubrics", e);
        }
        return arr.toString();
    }

    public String searchRubrics(String q) {
        JSONArray arr = new JSONArray();
        if (database == null || q == null || q.trim().isEmpty()) return "[]";
        q = q.trim();
        String qLower = q.toLowerCase();

        List<String> conditions = new ArrayList<>();
        List<String> params = new ArrayList<>();

        if (qLower.contains("headache")) {
            String alt = qLower.replace("headache", "").trim();
            if (!alt.isEmpty()) {
                conditions.add("(text LIKE ? AND (parent_path LIKE '%head%' OR full_path LIKE '%head%') AND text LIKE ?)");
                params.add("%pain%");
                params.add("%" + alt + "%");
            } else {
                conditions.add("(text LIKE ? AND (parent_path LIKE '%head%' OR full_path LIKE '%head%'))");
                params.add("%pain%");
            }
        }

        String[] words = q.split("\\s+");
        List<String> wordConds = new ArrayList<>();
        for (String w : words) {
            wordConds.add("(text LIKE ? OR parent_path LIKE ? OR full_path LIKE ?)");
            params.add("%" + w + "%");
            params.add("%" + w + "%");
            params.add("%" + w + "%");
        }
        if (!wordConds.isEmpty()) {
            StringBuilder sb = new StringBuilder("(");
            for (int i = 0; i < wordConds.size(); i++) {
                if (i > 0) sb.append(" AND ");
                sb.append(wordConds.get(i));
            }
            sb.append(")");
            conditions.add(sb.toString());
        }

        StringBuilder whereClause = new StringBuilder();
        for (int i = 0; i < conditions.size(); i++) {
            if (i > 0) whereClause.append(" OR ");
            whereClause.append(conditions.get(i));
        }

        String sql = "SELECT id, level, has_child, text, parent_path, full_path, remedy_count " +
                     "FROM rubrics WHERE " + whereClause + " ORDER BY remedy_count DESC, order_idx ASC LIMIT 80;";

        try (Cursor cursor = database.rawQuery(sql, params.toArray(new String[0]))) {
            while (cursor.moveToNext()) {
                JSONObject obj = new JSONObject();
                obj.put("id", cursor.getInt(0));
                obj.put("level", cursor.getInt(1));
                obj.put("has_child", cursor.getInt(2));
                obj.put("text", cursor.getString(3));
                obj.put("parent_path", cursor.getString(4));
                obj.put("full_path", cursor.getString(5));
                obj.put("remedy_count", cursor.getInt(6));
                arr.put(obj);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error in searchRubrics", e);
        }
        return arr.toString();
    }

    public String getRemedies(int rubricId) {
        JSONArray arr = new JSONArray();
        if (database == null) return "[]";
        String sql = "SELECT rr.remedy_id as id, rr.degree as degree, r.abbrev as abbrev, r.name as name, r.is_nosode as nosode " +
                     "FROM rubric_remedies rr " +
                     "JOIN remedies r ON rr.remedy_id = r.id " +
                     "WHERE rr.rubric_id = ? " +
                     "ORDER BY rr.degree DESC, r.abbrev ASC;";

        try (Cursor cursor = database.rawQuery(sql, new String[]{String.valueOf(rubricId)})) {
            while (cursor.moveToNext()) {
                JSONObject obj = new JSONObject();
                obj.put("id", cursor.getInt(0));
                obj.put("degree", cursor.getInt(1));
                obj.put("abbrev", cursor.getString(2));
                obj.put("name", cursor.getString(3));
                obj.put("nosode", cursor.getInt(4));
                arr.put(obj);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error in getRemedies", e);
        }
        return arr.toString();
    }

    public String getRemedyDetails(int remedyId) {
        JSONObject obj = new JSONObject();
        if (database == null) return "{}";
        String sql = "SELECT id, abbrev, name, origin, frequency, scientific_name, is_nosode as nosode, common_names, research_info " +
                     "FROM remedies WHERE id = ? LIMIT 1;";

        try (Cursor cursor = database.rawQuery(sql, new String[]{String.valueOf(remedyId)})) {
            if (cursor.moveToNext()) {
                obj.put("id", cursor.getInt(0));
                obj.put("abbrev", cursor.getString(1));
                obj.put("name", cursor.getString(2));
                obj.put("origin", cursor.getString(3));
                obj.put("frequency", cursor.getInt(4));
                obj.put("scientific_name", cursor.getString(5));
                obj.put("nosode", cursor.getInt(6));
                obj.put("common_names", cursor.getString(7));
                obj.put("research_info", cursor.getString(8));
                obj.put("images", new JSONArray());
                obj.put("sounds", new JSONArray());
            }
        } catch (Exception e) {
            Log.e(TAG, "Error in getRemedyDetails", e);
        }
        return obj.toString();
    }
}
