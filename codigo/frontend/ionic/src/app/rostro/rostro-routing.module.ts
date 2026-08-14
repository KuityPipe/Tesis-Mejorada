import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { RostroPage } from './rostro.page';

const routes: Routes = [
  {
    path: '',
    component: RostroPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class RostroPageRoutingModule {}
