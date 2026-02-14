package com.keycloak.qa.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

public class AdminConsolePage {

    private WebDriver driver;

    
    //private By realmSelectToggle = By.cssSelector("[data-testid='realmSelectToggle']");
    // Very stable admin console element
    private By sidebar = By.id("page-sidebar");

    public AdminConsolePage(WebDriver driver) {
        this.driver = driver;
    }

    public boolean waitUntilLoaded() {
    WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(20));
    try {
            wait.until(ExpectedConditions.urlContains("/admin/master/console/"));
            wait.until(ExpectedConditions.presenceOfElementLocated(sidebar));
            wait.until(ExpectedConditions.visibilityOfElementLocated(sidebar));
            return true;
    } catch (Exception e) {
            System.out.println("AdminConsolePage did not load. Current URL: " + driver.getCurrentUrl());
            return false;
        }
}

}
