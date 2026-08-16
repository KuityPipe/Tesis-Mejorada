import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { RostroPageRoutingModule } from './rostro-routing.module';
import { SharedModule } from '../shared/shared.module';

import { RostroPage } from './rostro.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    RostroPageRoutingModule,
    SharedModule
  ],
  declarations: [RostroPage]
})
export class RostroPageModule {}
