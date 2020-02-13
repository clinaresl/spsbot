literal numero
	23

literal irracional
	3.14159

literal apellidos
	"Apellidos"

literal formula
	"=C3+C4"

"vacuum-1.xlsx" : "Hoja 1" {
	$A2 "Nombre";
	$B2 literal.apellidos;

	$C3 23;
	$C4 3.14159;
	$C5 literal.formula;

	$D3 literal.numero;
	$D4 literal.irracional;
	$D5 "=$C4*$C3";

	$B7:$E7 right "--------";
}

