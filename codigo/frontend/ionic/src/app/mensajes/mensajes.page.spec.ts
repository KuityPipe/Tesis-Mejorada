import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { MensajesPage } from './mensajes.page';
import { SharedModule } from '../shared/shared.module';

describe('MensajesPage', () => {
  let component: MensajesPage;
  let fixture: ComponentFixture<MensajesPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MensajesPage],
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(MensajesPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
