Proiect Simulare Boids cu obstacole
===================================

Descriere:
---------
Un proiect simplu care simuleaza miscarea a n boids-uri respectand cele 3 legi ale simularii:
1) Separare: un boid va încerca sa evite aglomerarea / suprapunerea cu alți boids;
2) Alinierea: un boid va încerca să păstreze direcția medie de deplasare a boids din vecinătate
3) Coeziune: un boid va încerca sa se deplaseze către poziția medie a boids din vecinătate
Pe scurt se vor forma niste stoluri, iar fiecare boid individual va incerca sa ramana in acel stol pana va da de unul mai mare, in care caz devine parte de cel mai mare

Customizare:
-----------

-   WIDTH, HEIGHT - rezolutia jocului
-   NUM_BOIDS - numarul de obiecte
-   MAX_SPEED - modulul maxim al vitezei
-   MAX_FORCE - acceleratia maxima
-   NEIGH_DIST - raza de viziune a unui boid
-   SEPAR_DIST - distanta la care se activeaza forta de separare
-   OBSST_COUNT - numarul de obstacole generat pe ecran
-   AVOID_RADIUS, OBST_BUFFER - formeaza câmpul de respingere al obstacolelor, cand distanta este                                  mai mica decat adunarea celor doua constante, obiectul incepe să                                   vireze
- UI_W, UI_H - marimile panoului de control, pozitionat în colțul din dreapta jos
