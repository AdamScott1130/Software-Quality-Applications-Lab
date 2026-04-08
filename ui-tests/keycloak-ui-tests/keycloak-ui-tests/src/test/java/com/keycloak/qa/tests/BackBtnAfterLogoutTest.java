/* This file is about testing
   1. Verify that after logging out, using the browser Back button does not restore access to the protected page.
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


public class BackBtnAfterLogoutTest extends BaseTest {

    @Test
    public void browserBack_afterLogout_shouldNotReturnToAuthenticatedPage() {

        driver.get(ConfigReader.get("adminUrl"));

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

        driver.navigate().back(); // going back

        driver.navigate().refresh(); // to reload

        wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("kc-login")));

        String currentUrl = driver.getCurrentUrl();
        String pageTitle = driver.getTitle();
        // System.out.println("currentUrl: "+ currentUrl);
        // System.out.println("pageTitle: "+ pageTitle);

        Assert.assertTrue(
                pageTitle.contains("Sign in to Keycloak"),
                "Broswer stored back login page."
        );

        Assert.assertFalse(
                pageTitle.contains("Administration Console"),
                "Protected page became accessible after logout"
        );

        System.out.println("Test passed: Browser back does not restore authenticated session after logout.");
    }
}
