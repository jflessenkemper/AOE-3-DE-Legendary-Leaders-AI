# 🧠 Legendary Leaders AI

**Legendary Leaders AI** is a standalone Age of Empires III: Definitive Edition mod that combines the base civilizations with the playable revolution roster. Each nation is mapped to a themed leader personality and a clear battlefield identity.

*French note:* **Revolutionary France and Napoleonic France now use separate selectable civs.** Royal France remains the base French civ, while the two revolution-era French paths now have their own nation slots and card pools.

## 🏳️ Surrender

Surrender is currently an *AI-driven battlefield mechanic*, not a player button: damaged non-elite units can give up when elite support is gone, and they then move into the existing prison flow instead of instantly switching sides. If we add a proper surrender button later, the clean implementation is a dedicated tech or UI command that calls this same prison-transfer logic rather than creating a second surrender system.

## 🌍 Nation Guide

Portraits below match the current in-game nation portraits used by the mod. Flags are shown with small real-world flag markers for quick reading.

<details>
<summary><strong>Standard Nations (22)</strong></summary>

| Portrait | Flag | Nation | Leader | Playstyle |
| --- | --- | --- | --- | --- |
| <img src="resources/images/icons/singleplayer/cpai_avatar_aztecs_montezuma.png" alt="Montezuma II portrait" width="40"> | 🇲🇽 | Aztecs | Montezuma II | *Aggressive* imperial warbands with fast infantry pressure and coyote mobility. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_british_wellington.png" alt="Duke of Wellington portrait" width="40"> | 🇬🇧 | British | Duke of Wellington | *Defensive* manor-and-musketeer play with reliable artillery scaling. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_chinese_kangxi.png" alt="Kangxi Emperor portrait" width="40"> | 🇨🇳 | Chinese | Kangxi Emperor | *Balanced* banner-army macro with layered armies and steady siege support. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_dutch_maurice.png" alt="Maurice of Nassau portrait" width="40"> | 🇳🇱 | Dutch | Maurice of Nassau | *Defensive* bank economy with skirmisher-ruyter control. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_ethiopians_menelik.png" alt="Menelik II portrait" width="40"> | 🇪🇹 | Ethiopians | Menelik II | *Aggressive* modernization with strong infantry pressure and artillery follow-through. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_french_napoleon.png" alt="Napoleon Bonaparte portrait" width="40"> | 🇫🇷 | French | Napoleon Bonaparte | *Aggressive* imperial tempo with skirmisher-cuirassier power spikes. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_germans_frederick.png" alt="Frederick the Great portrait" width="40"> | 🇩🇪 | Germans | Frederick the Great | *Balanced* cavalry-mercenary warfare with strong timing pushes. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_haudenosaunee_hiawatha.png" alt="Hiawatha portrait" width="40"> | 🇨🇦 | Haudenosaunee | Hiawatha | *Balanced* confederacy warfare with early warband mass and siege pressure. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_hausa_usman.png" alt="Usman dan Fodio portrait" width="40"> | 🇳🇬 | Hausa | Usman dan Fodio | *Aggressive* influence-backed expansion with mobile raids. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_inca_pachacuti.png" alt="Pachacuti portrait" width="40"> | 🇵🇪 | Inca | Pachacuti | *Defensive* mountain empire with dense infantry and attritional control. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_indians_shivaji.png" alt="Shivaji Maharaj portrait" width="40"> | 🇮🇳 | Indians | Shivaji Maharaj | *Balanced* flexibility with strong infantry cores and sharp transitions. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_italians_garibaldi.png" alt="Giuseppe Garibaldi portrait" width="40"> | 🇮🇹 | Italians | Giuseppe Garibaldi | *Balanced* architect-command economy with flexible infantry-artillery play. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_japanese_tokugawa.png" alt="Tokugawa Ieyasu portrait" width="40"> | 🇯🇵 | Japanese | Tokugawa Ieyasu | *Defensive* shrine economy with disciplined timing windows. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_lakota_crazy_horse.png" alt="Crazy Horse portrait" width="40"> | 🇺🇸 | Lakota | Crazy Horse | *Aggressive* mounted mobility with constant raiding and map control. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_maltese_valette.png" alt="Jean Parisot de Valette portrait" width="40"> | 🇲🇹 | Maltese | Jean Parisot de Valette | *Defensive* fortress play with emplacements and stubborn infantry anchors. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_mexicans_hidalgo_base.png" alt="Miguel Hidalgo y Costilla portrait" width="40"> | 🇲🇽 | Mexicans | Miguel Hidalgo y Costilla | *Balanced* insurgent republic with adaptable armies and civic tempo. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_ottomans_suleiman.png" alt="Suleiman the Magnificent portrait" width="40"> | 🇹🇷 | Ottomans | Suleiman the Magnificent | *Aggressive* gunpowder tempo with Janissary pressure and artillery spikes. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_portuguese_henry.png" alt="Prince Henry the Navigator portrait" width="40"> | 🇵🇹 | Portuguese | Prince Henry the Navigator | *Defensive* town-center boom with strong ranged cores. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_russians_catherine.png" alt="Catherine the Great portrait" width="40"> | 🇷🇺 | Russians | Catherine the Great | *Aggressive* mass-army play with cheap infantry floods and blockhouse pressure. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_spanish_isabella.png" alt="Isabella I of Castile portrait" width="40"> | 🇪🇸 | Spanish | Isabella I of Castile | *Aggressive* shipment-led conquest with fast timing attacks. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_swedes_gustavus.png" alt="Gustavus Adolphus portrait" width="40"> | 🇸🇪 | Swedes | Gustavus Adolphus | *Aggressive* torp-and-timing warfare with Carolean mass. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_united_states_washington.png" alt="George Washington portrait" width="40"> | 🇺🇸 | United States | George Washington | *Balanced* republican flexibility with broad card options and steady scaling. |

</details>

<details>
<summary><strong>Revolution Nations (26)</strong></summary>

| Portrait | Flag | Nation | Leader | Playstyle |
| --- | --- | --- | --- | --- |
| <img src="resources/images/icons/singleplayer/cpai_avatar_americans_washington.png" alt="George Washington portrait" width="40"> | 🇺🇸 | Americans | Thomas Jefferson | *Balanced* statesman-general play with flexible infantry and measured artillery scaling. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_argentines_san_martin.png" alt="Jose de San Martin portrait" width="40"> | 🇦🇷 | Argentines | Jose de San Martin | *Aggressive* liberation cavalry with fast campaigning and mobile strikes. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_baja_californians_alvarado.png" alt="Juan Bautista Alvarado portrait" width="40"> | 🇲🇽 | Baja Californians | Juan Bautista Alvarado | *Aggressive* frontier raiding with cavalry-heavy harassment. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_barbary_barbarossa.png" alt="Hayreddin Barbarossa portrait" width="40"> | 🇱🇾 | Barbary | Hayreddin Barbarossa | *Aggressive* corsair warfare with trade disruption and raids. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_brazil_pedro_i.png" alt="Pedro I of Brazil portrait" width="40"> | 🇧🇷 | Brazil | Pedro I of Brazil | *Balanced* imperial combined arms with reliable artillery support. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_californians_vallejo.png" alt="Mariano Guadalupe Vallejo portrait" width="40"> | 🇺🇸 | Californians | Mariano Guadalupe Vallejo | *Defensive* frontier administration with trade-rich economy and careful cavalry response. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_canadians_brock.png" alt="Isaac Brock portrait" width="40"> | 🇨🇦 | Canadians | Isaac Brock | *Defensive* frontier line with forts and disciplined infantry-artillery play. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_central_americans_morazan.png" alt="Francisco Morazan portrait" width="40"> | 🇭🇳 | Central Americans | Francisco Morazan | *Balanced* federalist warfare with native alliances and steady tempo. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_chileans_ohiggins.png" alt="Bernardo O'Higgins portrait" width="40"> | 🇨🇱 | Chileans | Bernardo O'Higgins | *Balanced* republican army with disciplined infantry and fort support. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_columbians_bolivar.png" alt="Simon Bolivar portrait" width="40"> | 🇨🇴 | Columbians | Simon Bolivar | *Aggressive* liberator combined arms with forward bases and artillery pressure. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_egyptians_muhammad_ali.png" alt="Muhammad Ali Pasha portrait" width="40"> | 🇪🇬 | Egyptians | Muhammad Ali Pasha | *Balanced* reformer modernization with strong artillery and infrastructure. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_finnish_mannerheim.png" alt="Carl Gustaf Emil Mannerheim portrait" width="40"> | 🇫🇮 | Finnish | Carl Gustaf Emil Mannerheim | *Defensive* marshal doctrine with entrenched infantry-artillery play. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_french_canadians_papineau.png" alt="Louis-Joseph Papineau portrait" width="40"> | 🇨🇦 | French Canadians | Louis-Joseph Papineau | *Defensive* militia-reformer style with civic endurance and trade resilience. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_haitians_louverture.png" alt="Toussaint Louverture portrait" width="40"> | 🇭🇹 | Haitians | Toussaint Louverture | *Aggressive* revolutionary infantry with native-backed land pressure. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_hungarians_kossuth.png" alt="Lajos Kossuth portrait" width="40"> | 🇭🇺 | Hungarians | Lajos Kossuth | *Aggressive* nationalist combined arms with strong cavalry commitment. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_indonesians_diponegoro.png" alt="Prince Diponegoro portrait" width="40"> | 🇮🇩 | Indonesians | Prince Diponegoro | *Defensive* resistance warfare with patient trade-backed play. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_mayans_canek.png" alt="Jacinto Canek portrait" width="40"> | 🇲🇽 | Mayans | Jacinto Canek | *Aggressive* indigenous uprising with infantry and native swarms. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_mexicans_hidalgo.png" alt="Miguel Hidalgo y Costilla portrait" width="40"> | 🇲🇽 | Mexicans (Revolution) | Jose Maria Morelos | *Aggressive* insurgent offense with infantry-led attacks and rising momentum. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_napoleonic_france.png" alt="Napoleon Bonaparte portrait" width="40"> | 🇫🇷 | Revolutionary France | Maximilien Robespierre | *Aggressive* republican terror-state play with zeal, militia pressure, and anti-elite momentum. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_napoleonic_france.png" alt="Napoleon Bonaparte portrait" width="40"> | 🇫🇷 | Napoleonic France | Napoleon Bonaparte | *Aggressive* imperial tempo with heavy artillery, cavalry support, and forward-base escalation. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_peruvians_santa_cruz.png" alt="Andres de Santa Cruz portrait" width="40"> | 🇵🇪 | Peruvians | Andres de Santa Cruz | *Defensive* Andean marshal play with infantry lines and fort-backed control. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_rio_grande_canales_rosillo.png" alt="Antonio Canales Rosillo portrait" width="40"> | 🇲🇽 | Rio Grande | Antonio Canales Rosillo | *Aggressive* border-war mobility with fast cavalry raids. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_romanians_cuza.png" alt="Alexandru Ioan Cuza portrait" width="40"> | 🇷🇴 | Romanians | Alexandru Ioan Cuza | *Defensive* reformist combined arms with organized infantry-artillery pressure. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_south_africans_kruger.png" alt="Paul Kruger portrait" width="40"> | 🇿🇦 | South Africans | Paul Kruger | *Defensive* frontier command with trade leverage and stubborn strongpoints. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_texians_sam_houston.png" alt="Sam Houston portrait" width="40"> | 🇺🇸 | Texians | Sam Houston | *Defensive* frontier counterpunch with fortified positions. |
| <img src="resources/images/icons/singleplayer/cpai_avatar_yucatan_carrillo_puerto.png" alt="Felipe Carrillo Puerto portrait" width="40"> | 🇲🇽 | Yucatan | Felipe Carrillo Puerto | *Balanced* regional resistance with native support and stubborn territorial play. |

</details>
