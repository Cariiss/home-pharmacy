package ru.homepharmacy.ui

import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument

@Composable
fun AppNavigation() {
    val nav = rememberNavController()
    val idArg = listOf(navArgument("id") { type = NavType.IntType })

    NavHost(nav, startDestination = "packages") {
        composable("packages") {
            PackagesScreen(
                onOpen = { id -> nav.navigate("package/$id") },
                onAdd = { nav.navigate("package_form/0") },
                onMedicines = { nav.navigate("medicines") },
                onSettings = { nav.navigate("settings") },
            )
        }
        composable("package/{id}", idArg) {
            PackageDetailScreen(
                onBack = { nav.popBackStack() },
                onEdit = { id -> nav.navigate("package_form/$id") },
            )
        }
        // id = 0 — новая упаковка, иначе редактирование
        composable("package_form/{id}", idArg) {
            PackageFormScreen(
                onBack = { nav.popBackStack() },
                onMedicines = { nav.navigate("medicines") },
            )
        }
        composable("medicines") { MedicinesScreen(onBack = { nav.popBackStack() }) }
        composable("settings") { SettingsScreen(onBack = { nav.popBackStack() }) }
    }
}
