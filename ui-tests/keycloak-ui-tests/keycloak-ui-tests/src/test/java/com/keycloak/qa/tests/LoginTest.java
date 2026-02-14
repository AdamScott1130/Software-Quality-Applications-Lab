package com.keycloak.qa.tests;

import com.keycloak.qa.base.BaseTest;
import com.keycloak.qa.pages.AdminConsolePage;
import com.keycloak.qa.pages.LoginPage;
import com.keycloak.qa.utils.ConfigReader;
import org.testng.Assert;
import org.testng.annotations.Test;

public class LoginTest extends BaseTest {

    @Test
    public void validAdminLogin_shouldReachAdminConsole() {

        driver.get(ConfigReader.get("adminUrl")); // Keycloak will redirect to login automatically

        LoginPage loginPage = new LoginPage(driver);
        loginPage.login(ConfigReader.get("username"), ConfigReader.get("password"));

        AdminConsolePage adminConsole = new AdminConsolePage(driver);
        System.out.println("After login URL: " + driver.getCurrentUrl());
        System.out.println("Page title: " + driver.getTitle());

        Assert.assertFalse(loginPage.isLoginErrorVisible(), "Login error shown for valid credentials");
        Assert.assertTrue(adminConsole.waitUntilLoaded(), "Admin console did not load after login");
    }

    @Test
    public void invalidLogin_shouldShowError() {

        driver.get(ConfigReader.get("adminUrl"));

        LoginPage loginPage = new LoginPage(driver);
        loginPage.login("wrong", "wrong");

        Assert.assertTrue(loginPage.isLoginErrorVisible(), "Expected login error not shown");
    }
}
