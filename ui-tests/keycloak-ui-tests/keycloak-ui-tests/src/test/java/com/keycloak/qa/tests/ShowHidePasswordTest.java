/* This file is about testing
   1. Log in page show/hide toggle works
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


public class ShowHidePasswordTest extends BaseTest {

    @Test
    public void showHidePassword() {

        driver.get(ConfigReader.get("adminUrl"));

        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        WebElement passwordField = wait.until(
                ExpectedConditions.visibilityOfElementLocated(By.id("password"))
        );

        passwordField.sendKeys("Test123");

        WebElement toggleButton = wait.until(
                ExpectedConditions.elementToBeClickable(
                        By.xpath("//button[contains(@class,'pf-v5-c-button') and (@aria-label='Show password' or @aria-label='Hide password')]")
                )
        );

        Assert.assertEquals(passwordField.getAttribute("type"), "password", "Password should be hidden by default");

        toggleButton.click();
        Assert.assertEquals(passwordField.getAttribute("type"), "text", "Password should be visible after first click");

        toggleButton.click();
        Assert.assertEquals(passwordField.getAttribute("type"), "password", "Password should be hidden again after second click");

        System.out.println("Test passed: Show/hide password works correctly.");
    }

}
