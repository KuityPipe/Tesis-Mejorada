import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { PagosPage } from './pagos.page';
import { SharedModule } from '../../shared/shared.module';

describe('PagosPage', () => {
  let component: PagosPage;
  let fixture: ComponentFixture<PagosPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PagosPage],
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(PagosPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
