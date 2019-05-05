#encoding "utf-8"
#GRAMMAR_ROOT Main

Main -> S;

Act -> Word<kwtype=improve_verbs, rt, gram="S">;

Obj -> Noun<gram="gen">;
Obj -> Adj+[gn-agr] Obj<rt> Word<gram="gen">*[gn-agr];
Obj -> Adj*[gn-agr] Obj<rt> Word<gram="gen">+[gn-agr];
Obj -> Obj SimConjAnd Obj;

Con -> Prep Word<GU=[ins]|[abl]>+[gn-agr];
Con -> Con<rt> Word<gram="gen">+[gn-agr];
Con -> Con<rt> SimConjAnd Word<GU=[ins]>+[gn-agr];



// Полное предложение
S -> Act interp(AOC.Action) Obj interp(AOC.Object::not_norm) (Con interp(AOC.Condit));


//S -> (Sbj<sp-agr[1]> interp(SAO.Subject)) AnyWord<cut>* Word<kwtype=conn_verbs, rt, sp-agr[1], gram="A"> interp(SAO.Action) PR Noun<gram="ins"> interp(SAO.Object);
//S -> Noun<gram="nom", sp-agr[1]> interp(SAO.Subject) 'и' Noun<gram="nom", sp-agr[1]> interp(SAO.Subject) Word<kwtype=conn_verbs, rt, gram="V",sp-agr[1]> interp(SAO.Action) AnyWord<cut>* PR AnyWord<cut>* Obj<gram="ins"> interp(SAO.Object);
