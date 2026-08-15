import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';

import { authGuard } from './core/auth-guard';

// `loadChildren` con un `import()` dinámico es lazy-loading: el código de
// cada página (y sus dependencias) recién se descarga cuando el usuario
// navega ahí, no en el bundle inicial. `canActivate: [authGuard]` corre el
// guard antes de permitir esa navegación (ver core/auth-guard.ts).
const routes: Routes = [
  {
    path: 'home',
    loadChildren: () => import('./home/home.module').then( m => m.HomePageModule),
    canActivate: [authGuard],
  },
  {
    // Landing pública (marketing + búsqueda rápida), equivalente Ionic de
    // `/` (paginicio_view) — distinta de `/catalogo` (listado completo,
    // equivalente de `/servicios/`) y de `/home` (dashboard autenticado,
    // equivalente de `/inicio/`), mismo criterio de 3 rutas separadas que
    // usa el sitio Django.
    path: '',
    loadChildren: () => import('./inicio/inicio.module').then( m => m.InicioPageModule),
  },
  {
    path: 'login',
    loadChildren: () => import('./login/login.module').then( m => m.LoginPageModule)
  },
  {
    path: 'catalogo',
    loadChildren: () => import('./catalogo/catalogo.module').then( m => m.CatalogoPageModule)
  },
  {
    path: 'acerca-de-nosotros',
    loadChildren: () => import('./acerca/acerca.module').then( m => m.AcercaPageModule)
  },
  {
    path: 'contacto',
    loadChildren: () => import('./contacto/contacto.module').then((m) => m.ContactoPageModule)
  },
  {
    path: 'registro',
    loadChildren: () => import('./registro/registro.module').then( m => m.RegistroPageModule)
  },
  {
    path: 'perfil/editar',
    loadChildren: () => import('./perfil/editar/editar.module').then( m => m.EditarPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'perfil/proveedor',
    loadChildren: () => import('./perfil/proveedor/proveedor.module').then( m => m.ProveedorPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'perfil/publicaciones',
    loadChildren: () => import('./perfil/publicaciones/publicaciones.module').then( m => m.PublicacionesPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'preferencias',
    loadChildren: () => import('./preferencias/preferencias.module').then( m => m.PreferenciasPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'recuperar',
    loadChildren: () => import('./recuperar/recuperar.module').then( m => m.RecuperarPageModule)
  },
  {
    path: 'reservas',
    loadChildren: () => import('./reservas/reservas.module').then( m => m.ReservasPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'contratacion/:id',
    loadChildren: () => import('./contratacion/detalle/detalle.module').then( m => m.DetallePageModule),
    canActivate: [authGuard],
  },
  {
    // Sin authGuard: Transbank/Khipu redirigen acá directo, y el token JWT
    // de la sesión Ionic puede haber quedado vencido durante el rato que
    // el usuario estuvo fuera de la SPA (ver Pagos.confirmarWebpay/estadoKhipu).
    path: 'pago/webpay/retorno',
    loadChildren: () => import('./pago/webpay/retorno/retorno.module').then( m => m.RetornoPageModule),
  },
  {
    path: 'pago/khipu/retorno/:id',
    loadChildren: () => import('./pago/khipu/retorno/retorno.module').then( m => m.RetornoPageModule),
  },
  {
    path: 'biometria',
    loadChildren: () => import('./biometria/biometria.module').then( m => m.BiometriaPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'rostro',
    loadChildren: () => import('./rostro/rostro.module').then( m => m.RostroPageModule),
    canActivate: [authGuard],
  },
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule { }
