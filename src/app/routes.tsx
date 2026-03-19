import React from "react";
import { createBrowserRouter } from "react-router";
import { Auth } from "./pages/Auth";
import { DashboardLayout } from "./components/DashboardLayout";
import { DashboardHome } from "./pages/DashboardHome";
import { FeaturePage } from "./pages/FeaturePage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Auth,
  },
  {
    path: "/dashboard",
    Component: DashboardLayout,
    children: [
      {
        index: true,
        Component: DashboardHome,
      },
      {
        path: ":featureId",
        Component: FeaturePage,
      },
    ],
  },
]);
