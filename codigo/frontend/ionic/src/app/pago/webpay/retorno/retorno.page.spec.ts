import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { RetornoPage } from './retorno.page';
import { SharedModule } from '../../../shared/shared.module';

describe('RetornoPage (webpay)', () => {
  let component: RetornoPage;
  let fixture: ComponentFixture<RetornoPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [RetornoPage],
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(RetornoPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
