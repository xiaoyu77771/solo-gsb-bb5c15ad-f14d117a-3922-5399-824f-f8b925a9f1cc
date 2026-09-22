import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage.jsx";
import EventPage from "./pages/EventPage.jsx";
import RevealPage from "./pages/RevealPage.jsx";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/event/:eventId" element={<EventPage />} />
        <Route path="/r/:token" element={<RevealPage />} />
        <Route path="*" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
