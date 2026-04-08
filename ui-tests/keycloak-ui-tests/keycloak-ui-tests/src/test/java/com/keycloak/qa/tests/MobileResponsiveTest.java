/* This file is about testing
   1. Responsive design for three devices. The purpose is to make sure UI display is okay for other screen than a laptop/desktop.
*/

package com.keycloak.qa.tests;

import com.keycloak.qa.base.BaseTest;
import com.keycloak.qa.utils.ConfigReader;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.Test;
import java.util.HashMap;
import java.util.Map;
import java.time.Duration;


public class MobileResponsiveTest extends BaseTest {

    @Test
    public void testMobileView_shouldDisplayLoginElements() {

        int[][] screens = {
                {375, 812}, //iPhone
                {360, 800}, //Android
                {768, 1024} //Tablet
        };

        for (int[] size: screens){
            int screenWidth = size[0];
            int screenHeight = size[1];

            ChromeDriver cDriver = (ChromeDriver) driver;

            Map<String,Object> deviceSizes = new HashMap<>();
            deviceSizes.put("width", screenWidth);
            deviceSizes.put("height", screenHeight);
            deviceSizes.put("deviceScaleFactor",2);
            deviceSizes.put("mobile",true);

            cDriver.executeCdpCommand("Emulation.setDeviceMetricsOverride",deviceSizes);

            driver.get(ConfigReader.get("adminUrl"));

            WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

            WebElement username = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("username")));
            WebElement password = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("password")));
            WebElement loginBtn = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("kc-login")));

            Assert.assertTrue(username.isDisplayed());
            Assert.assertTrue(password.isDisplayed());
            Assert.assertTrue(loginBtn.isDisplayed());

            System.out.println("Test passed: Responsive view with given sizes.");
        }
    }
}
