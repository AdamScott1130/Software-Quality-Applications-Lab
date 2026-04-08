/* This file is about testing
   1. Input field requirements are in place at login page
*/

package com.keycloak.qa.tests;

import com.keycloak.qa.base.BaseTest;
import com.keycloak.qa.utils.ConfigReader;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.time.Duration;


public class RequiredValueValidationTest extends BaseTest {

    @Test
    public void emptyLogin_shouldShowError() {

        driver.get(ConfigReader.get("adminUrl"));

        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        WebElement loginBtn = wait.until(
                ExpectedConditions.elementToBeClickable(By.id("kc-login"))
        );
        loginBtn.click();

        WebElement username = wait.until(
                ExpectedConditions.visibilityOfElementLocated(By.id("username"))
        );
        WebElement password = wait.until(
                ExpectedConditions.visibilityOfElementLocated(By.id("password"))
        );

        Assert.assertTrue(username.isDisplayed(), "Username field is not visible");
        Assert.assertTrue(password.isDisplayed(), "Password field is not visible");

        String pageSource = driver.getPageSource();

        Assert.assertTrue(
                pageSource.contains("required") || pageSource.contains("Required") ||
                        pageSource.contains("invalid") || pageSource.contains("Invalid"),
                "Validation error was not shown for empty login"
        );
        System.out.println("Test passed: Validation message shown for empty login.");
    }
}
