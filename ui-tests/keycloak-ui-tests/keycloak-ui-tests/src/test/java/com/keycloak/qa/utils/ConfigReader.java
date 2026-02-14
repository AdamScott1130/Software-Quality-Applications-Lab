package com.keycloak.qa.utils;

import java.io.FileInputStream;
import java.util.Properties;

public class ConfigReader {

    private static final Properties props = new Properties();
    private static boolean loaded = false;

    public static void load() {
        if (loaded) return;

        try (FileInputStream fis = new FileInputStream("src/test/resources/config.properties")) {
            props.load(fis);
            loaded = true;
        } catch (Exception e) {
            throw new RuntimeException("Could not load config.properties", e);
        }
    }

    public static String get(String key) {
        return props.getProperty(key);
    }
}
