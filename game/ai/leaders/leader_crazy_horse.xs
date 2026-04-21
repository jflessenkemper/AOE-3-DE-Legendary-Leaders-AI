//==============================================================================
/* leader_crazy_horse.xs

   Tasunke Witko (Crazy Horse) - Oglala Lakota war chief personality.

   Historical doctrine:
     - Mounted plains warfare: Lakota war bands fought as horse archers and
       lance cavalry. Mapped to a near-pure cavalry composition with
       almost no static infantry weight.
     - Little Bighorn (1876): Crazy Horse and Sitting Bull crushed Custer
       through encirclement and overwhelming mass cavalry. Mapped to a
       very aggressive baseline (offense bias near maximum) and a forward
       commitment from Discovery on.
     - Buffalo economy: Lakota civ trades static structures for tipi
       mobility and Buffalo hunts. Mapped to the Mobile Frontier Scatter
       style and a very negative Trade Route lean.
     - Native confederation: Cheyenne, Arapaho, and Dakota allies. Mapped
       to a strong Native Treaty bias.
     - Wakina Rifle, Cetan Bowman, Axe Rider, Tashunke Prowler - the
       Lakota army is fast skirmish-cavalry through and through. No
       artillery, no fortress doctrine.
*/
//==============================================================================

bool gCrazyHorseRulesEnabled = false;

void initLeaderCrazyHorse(void)
{
   llVerboseEcho("Legendary Leaders: activating Crazy Horse personality.");

   llSetAggressivePersonality();
   btRushBoom = 0.4;              // Almost no boom; the warpath opens immediately.
   btOffenseDefense = 0.85;       // Maximum offensive lean of any standard nation.
   btBiasTrade = -0.55;
   btBiasNative = 0.55;
   llSetMilitaryFocus(0.15, 0.85, -0.3);  // Cavalry totem.

   // LL-BUILD-STYLE-BEGIN
   llUseSteppeCavalryWedgeStyle(0);
   // LL-BUILD-STYLE-END
   llSetLeaderTacticalDoctrine(0.55, 0.45, 2, 2.5);

   cvOkToBuildForts = false;      // Lakota do not turtle.
   cvMaxTowers = 2;
   cvMaxArmyPop = 110;

   gCrazyHorseRulesEnabled = true;
   llLogLeaderState("Crazy Horse initialized");
}

//------------------------------------------------------------------------------
// Discovery: Buffalo camp. Tipi sprawl, native trade post; the war
// council assembles immediately after.
//------------------------------------------------------------------------------
rule crazyHorseBuffaloCamp
inactive
minInterval 55
{
   llLogRuleTick("crazyHorseBuffaloCamp");
   if (gCrazyHorseRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() <= cAge1)
   {
      btRushBoom = 0.1;
      btBiasNative = 0.7;
      cvMinNumVills = 14;
   }
}

//------------------------------------------------------------------------------
// Colonial: Running fight. Axe Rider and Cetan Bowman pressure on enemy
// villager and trade lines from Colonial onward.
//------------------------------------------------------------------------------
rule crazyHorseRunningFight
inactive
minInterval 45
{
   llLogRuleTick("crazyHorseRunningFight");
   if (gCrazyHorseRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() == cAge2)
   {
      btRushBoom = 0.15;
      btOffenseDefense = 0.9;
      btBiasInf = 0.0;
      btBiasCav = 0.95;            // Axe Rider and Cetan as the hammer.
      btBiasArt = -0.6;
      llEnableForwardBaseStyle();
   }
}

//------------------------------------------------------------------------------
// Fortress: Wakina horse archers. Wakina Rifle Riders and Tashunke Prowler
// mass form the field army; Dog Soldier shock arm.
//------------------------------------------------------------------------------
rule crazyHorseWakinaWar
inactive
minInterval 50
{
   llLogRuleTick("crazyHorseWakinaWar");
   if (gCrazyHorseRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() == cAge3)
   {
      btOffenseDefense = 0.95;
      btBiasInf = 0.1;
      btBiasCav = 1.0;
      btBiasArt = -0.5;
      cvMaxArmyPop = 125;
   }
}

//------------------------------------------------------------------------------
// Industrial: Bighorn war. Maximum Wakina / Tashunke / Axe Rider mass.
// Native treaty pulled to the limit. The plains burn.
//------------------------------------------------------------------------------
rule crazyHorseBighornWar
inactive
minInterval 65
{
   llLogRuleTick("crazyHorseBighornWar");
   if (gCrazyHorseRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() == cAge4)
   {
      btOffenseDefense = 1.0;
      btBiasInf = 0.15;
      btBiasCav = 1.0;
      btBiasArt = -0.4;
      btBiasNative = 0.7;
      cvMaxArmyPop = 140;
      llEnableForwardBaseStyle();
   }
}

//------------------------------------------------------------------------------
// Imperial: Lakota host - all cavalry, all native, no quarter. The
// largest possible mounted host the engine will field.
//------------------------------------------------------------------------------
rule crazyHorseLakotaHost
inactive
minInterval 80
{
   llLogRuleTick("crazyHorseLakotaHost");
   if (gCrazyHorseRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge5)
   {
      btOffenseDefense = 1.0;
      btBiasInf = 0.2;
      btBiasCav = 1.0;
      btBiasArt = -0.2;
      btBiasNative = 0.8;
      cvMaxArmyPop = 155;
   }
}

void enableLeaderCrazyHorseRules(void)
{
   if (gCrazyHorseRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("crazyHorseBuffaloCamp");
   xsEnableRule("crazyHorseRunningFight");
   xsEnableRule("crazyHorseWakinaWar");
   xsEnableRule("crazyHorseBighornWar");
   xsEnableRule("crazyHorseLakotaHost");
}
