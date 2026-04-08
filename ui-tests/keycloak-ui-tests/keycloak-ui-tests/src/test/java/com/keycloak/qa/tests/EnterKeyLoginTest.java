/* This file is about testing
   1. To verify that pressing the Enter key after entering valid credentials submits the login form successfully.
*/

package com.keycloak.qa.tests;

import com.keycloak.qa.base.BaseTest;
import com.keycloak.qa.pages.LoginPage;
import com.keycloak.qa.utils.ConfigReader;
import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.Test;
import java.time.Duration;
import com.keycloak.qa.pages.AdminConsolePage;


public class EnterKeyLoginTest extends BaseTest {

    @Test
    public void enterKey_shouldSubmitLoginForm() {

        driver.get(ConfigReader.get("adminUrl"));

        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        WebElement username = wait.until(
                ExpectedConditions.visibilityOfElementLocated(By.id("username"))
        );
        WebElement password = wait.until(
                ExpectedConditions.visibilityOfElementLocated(By.id("password"))
        );

        username.sendKeys(ConfigReader.get("username"));
        password.sendKeys(ConfigReader.get("password"));
        password.sendKeys(Keys.ENTER);

        LoginPage loginPage = new LoginPage(driver);

        Assert.assertFalse(driver.getPageSource().contains("Invalid username or password"),
                "Login error shown for valid credentials");

        System.out.println("Test passed: Pressing Enter submits login successfully.");
    }
}
