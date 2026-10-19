// Issue #75: a destructive verb is recognized as a whole word, never as a substring
// of an ordinary one -- "borrador" contains "borra" and "preliminares" contains
// "elimina", and neither asks for anything to be deleted.
import assert from 'node:assert/strict';
import path from 'node:path';
import test from 'node:test';
import { createJiti } from 'jiti';
const jiti=createJiti(import.meta.url);
const engineDir=path.resolve('skills/_core/deliberation/engine');
const {resolveIntent}=await jiti.import(path.join(engineDir,'intent-resolver.ts'));

test('ordinary words that merely contain a destructive verb are not a DELETE',()=>{
	for(const instruction of [
		'revisá el borrador del párrafo tercero',
		'mejora la redacción de los resultados preliminares',
		'los borradores anteriores tenían otra notación',
		'esa quitanieves aparece en el ejemplo',
	])
		assert.notEqual(resolveIntent(instruction).intent,'DELETE',instruction);
});

test('an actual delete request is still a DELETE',()=>{
	for(const instruction of [
		'elimina el párrafo tercero',
		'eliminá el lema 2',
		'borra la segunda oración del párrafo tercero',
		'bórralo del párrafo tercero',
		'quita la nota al pie del párrafo tercero',
		'suprime la definición 4',
		'remueve el corolario 1',
		'hay que eliminar el párrafo tercero',
	])
		assert.equal(resolveIntent(instruction).intent,'DELETE',instruction);
});

test('a move removes its source, so it is never selected by a substring either',()=>{
	for(const instruction of [
		'revisa el contenido trasladado al apéndice',
		'el lema conmueve al lector',
	])
		assert.notEqual(resolveIntent(instruction).intent,'MOVE',instruction);
	for(const instruction of [
		'mueve el lema 2 a la sección 3',
		'traslada el lema 2 a la sección 3',
		'hay que trasladar el lema 2 a la sección 3',
		'trasládalo a la sección 3',
	])
		assert.equal(resolveIntent(instruction).intent,'MOVE',instruction);
});

test('a borrador mention never turns an otherwise unclear request destructive',()=>{
	const r=resolveIntent('el borrador del párrafo tercero');
	assert.notEqual(r.intent,'DELETE');
});
