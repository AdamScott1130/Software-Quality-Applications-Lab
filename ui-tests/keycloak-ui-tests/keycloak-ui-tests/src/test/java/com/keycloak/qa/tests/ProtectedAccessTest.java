/* This file is about testing
   1. Trying to access admin url without logging in
*/

package com.keycloak.qa.tests;

import com.keycloak.qa.base.BaseTest;
import com.keycloak.qa.pages.AdminConsolePage;
import com.keycloak.qa.pages.LoginPage;
import com.keycloak.qa.utils.ConfigReader;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.time.Duration;

public class ProtectedAccessTest extends BaseTest {

    @Test
    public void testProtectedUrl_shouldRedirectToLoginPage() {

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
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("username")));

        String testUrl = ConfigReader.get("adminUrl")+"/master/clients";
        driver.get(testUrl);

        Boolean checkProtectedId = driver.findElements(By.id("nav-item-realms")).size() >0;

        if (checkProtectedId) {
            System.out.println("Test fail: User still has access to protected url");
        } else {
            System.out.println("Test pass: Session invalidated. User is redirected.");
        }

        Assert.assertFalse(
                checkProtectedId,
                "Security issue: User still have access to protected url."
        );

    }
}
