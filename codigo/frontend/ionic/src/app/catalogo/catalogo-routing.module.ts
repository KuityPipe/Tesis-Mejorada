import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { authGuard } from '../core/auth-guard';
import { CatalogoPage } from './catalogo.page';

const routes: Routes = [
  {
    path: '',
    component: CatalogoPage
  },
  {
    // Ruta literal 'crear' antes de ':id' — Angular matchea rutas en el
    // orden del array, así que 'crear' nunca se interpreta como un pk
    // (mismo criterio que /servicios/crear/ vs /servicios/<pk>/ en Django,
    // que tampoco chocan porque <pk> es un IntConverter).
    path: 'crear',
    loadChildren: () => import('./crear/crear.module').then( m => m.CrearPageModule),
    canActivate: [authGuard],
  },
  {
    // :id es el pk de Publicaciones — DetallePage lo lee de la ruta con
    // ActivatedRoute, no de un query param.
    path: ':id',
    loadChildren: () => import('./detalle/detalle.module').then( m => m.DetallePageModule)
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class CatalogoPageRoutingModule {}
