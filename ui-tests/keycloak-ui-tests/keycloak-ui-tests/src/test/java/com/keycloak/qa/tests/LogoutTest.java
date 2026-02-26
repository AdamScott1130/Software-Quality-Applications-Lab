/* This file is about testing logout
   1. Login first
   2. Log out
*/

package com.keycloak.qa.tests;

import com.keycloak.qa.base.BaseTest;
import com.keycloak.qa.pages.LoginPage;
import com.keycloak.qa.utils.ConfigReader;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.time.Duration;

public class LogoutTest extends BaseTest {

    @Test
    public void testLogOut_shouldRedirectToLoginPage() {

        driver.get(ConfigReader.get("adminUrl")); // Keycloak will redirect to login automatically

        LoginPage loginPage = new LoginPage(driver);
        loginPage.login(ConfigReader.get("username"), ConfigReader.get("password"));

        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        // click Admin menu to be able to see log out
        WebElement adminDropdown = wait.until(
                ExpectedConditions.elementToBeClickable(
                        By.xpath("//button[contains(@class,'pf-v5-c-menu-toggle')]//span[text()='admin']")
                )
        );
        adminDropdown.click();

        // click log out
        WebElement signOut = wait.until(
                ExpectedConditions.elementToBeClickable(
                        By.xpath("//button[contains(@class, 'pf-v5-c-menu__item')]//span[text()='Sign out']")
                )
        );
        signOut.click();

        wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("kc-login")));

        String pageTitle = driver.getTitle();

        Assert.assertTrue(pageTitle.contains(("Sign in")),"Logout succeed");
        Assert.assertFalse(pageTitle.contains("Administration Console"),"Logout failed");

        System.out.println("Test passed: Logout succeed. Current Page"+ pageTitle);

    }
}
