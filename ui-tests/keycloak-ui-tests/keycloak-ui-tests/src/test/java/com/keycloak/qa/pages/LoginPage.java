package com.keycloak.qa.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

public class LoginPage {

    private WebDriver driver;

    private By username = By.id("username");
    private By password = By.id("password");
    private By loginButton = By.id("kc-login");

    // More reliable than input-error across Keycloak versions
    private By errorAlert = By.cssSelector(".pf-c-alert__title, .kc-feedback-text");

    public LoginPage(WebDriver driver) {
        this.driver = driver;
    }

    public void login(String user, String pass) {
        driver.findElement(username).clear();
        driver.findElement(username).sendKeys(user);

        driver.findElement(password).clear();
        driver.findElement(password).sendKeys(pass);

        driver.findElement(loginButton).click();
    }

    public boolean isLoginErrorVisible() {
        return driver.findElements(errorAlert).size() > 0;
    }
}
