import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { RostroPage } from './rostro.page';
import { SharedModule } from '../shared/shared.module';

describe('RostroPage', () => {
  let component: RostroPage;
  let fixture: ComponentFixture<RostroPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [RostroPage],
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(RostroPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
