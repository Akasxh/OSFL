import Nav from "./components/Nav.jsx";
import Hero from "./components/Hero.jsx";
import Marquee from "./components/Marquee.jsx";
import TheQueue from "./components/TheQueue.jsx";
import TheArc from "./components/TheArc.jsx";
import CoreMechanic from "./components/CoreMechanic.jsx";
import SkillsFolder from "./components/SkillsFolder.jsx";
import SimulationLab from "./components/SimulationLab.jsx";
import DigitalTwin from "./components/DigitalTwin.jsx";
import WhoItsFor from "./components/WhoItsFor.jsx";
import Philosophy from "./components/Philosophy.jsx";
import CTA from "./components/CTA.jsx";
import FAQ from "./components/FAQ.jsx";
import Footer from "./components/Footer.jsx";

export default function App() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <Marquee />
        <TheQueue />
        <TheArc />
        <CoreMechanic />
        <SkillsFolder />
        <SimulationLab />
        <DigitalTwin />
        <WhoItsFor />
        <Philosophy />
        <CTA />
        <FAQ />
      </main>
      <Footer />
    </>
  );
}
